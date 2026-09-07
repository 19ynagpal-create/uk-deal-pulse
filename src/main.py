import os
import re
import json
import time
from datetime import datetime, timezone
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup
from google import genai
from google.genai import errors

from discovery import discover_candidates


# =========================================================
# CONFIG
# =========================================================

GEMINI_API_KEY = os.environ["GEMINI_API_KEY"]
SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_KEY = os.environ["SUPABASE_SERVICE_ROLE_KEY"]

GEMINI_MODEL = "gemini-3.5-flash-lite"

INVESTEGATE_BASE = "https://www.investegate.co.uk"
INVESTEGATE_RNS = "https://www.investegate.co.uk/source/RNS"

# Scan recent RNS pages.
# Once per week, this is still very low usage.
MAX_RNS_PAGES = 25

REQUEST_TIMEOUT = 30

HEADERS = {
    "User-Agent": (
        "UKDealPulse/1.0 "
        "(educational UK M&A research project)"
    )
}

TAKEOVER_KEYWORDS = (
    "acquisition",
    "recommended cash",
    "recommended offer",
    "firm offer",
    "cash offer",
    "takeover",
    "scheme of arrangement",
    "offer for",
    "merger",
    "rule 2.7",
)

client = genai.Client(api_key=GEMINI_API_KEY)


# =========================================================
# HELPERS
# =========================================================

def db_headers():
    return {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
    }


def normalize_name(value):
    if not value:
        return ""

    value = value.lower()

    replacements = [
        "public limited company",
        "plc",
        "limited",
        "ltd",
        "incorporated",
        "inc",
        "holdings",
        "group",
    ]

    for item in replacements:
        value = value.replace(item, " ")

    value = re.sub(r"[^a-z0-9 ]", " ", value)
    value = re.sub(r"\s+", " ", value)

    return value.strip()


def company_matches(candidate_name, text):
    """
    Conservative fuzzy-ish company matching.

    We do not require the entire legal company suffix to match.
    """

    candidate = normalize_name(candidate_name)
    haystack = normalize_name(text)

    if not candidate or not haystack:
        return False

    if candidate in haystack:
        return True

    candidate_words = [
        w for w in candidate.split()
        if len(w) >= 4
    ]

    if not candidate_words:
        return False

    hits = sum(
        1 for word in candidate_words
        if word in haystack
    )

    required = max(
        1,
        int(len(candidate_words) * 0.7)
    )

    return hits >= required


# =========================================================
# PROCESSED SOURCES
# =========================================================

def source_already_processed(url):
    r = requests.get(
        f"{SUPABASE_URL}/rest/v1/processed_sources",
        headers=db_headers(),
        params={
            "select": "id,processing_status",
            "source_url": f"eq.{url}",
            "limit": "1",
        },
        timeout=REQUEST_TIMEOUT,
    )

    r.raise_for_status()
    rows = r.json()

    if not rows:
        return False

    status = rows[0].get("processing_status")

    # Allow failed jobs to retry later.
    return status != "error"


def mark_processed(
    url,
    title,
    status,
    error_message=None,
):
    payload = {
        "source_url": url,
        "source_title": title,
        "processed_at": datetime.now(
            timezone.utc
        ).isoformat(),
        "processing_status": status,
        "error_message": error_message,
    }

    r = requests.post(
        (
            f"{SUPABASE_URL}/rest/v1/"
            "processed_sources"
            "?on_conflict=source_url"
        ),
        headers={
            **db_headers(),
            "Prefer": (
                "resolution=merge-duplicates,"
                "return=minimal"
            ),
        },
        json=payload,
        timeout=REQUEST_TIMEOUT,
    )

    r.raise_for_status()


# =========================================================
# INVESTEGATE DISCOVERY
# =========================================================

def scrape_rns_listing_page(page_number):
    """
    Collect announcement links from a recent Investegate
    RNS listing page.
    """

    url = f"{INVESTEGATE_RNS}?page={page_number}"

    r = requests.get(
        url,
        headers=HEADERS,
        timeout=REQUEST_TIMEOUT,
    )

    r.raise_for_status()

    soup = BeautifulSoup(
        r.text,
        "html.parser",
    )

    results = []
    seen = set()

    for link in soup.find_all(
        "a",
        href=True,
    ):
        href = link.get("href", "")

        if "/announcement/" not in href:
            continue

        full_url = urljoin(
            INVESTEGATE_BASE,
            href,
        )

        if full_url in seen:
            continue

        title = link.get_text(
            " ",
            strip=True,
        )

        parent_text = ""

        parent = link.parent

        if parent:
            parent_text = parent.get_text(
                " ",
                strip=True,
            )

            # Often useful context is higher up the row.
            if parent.parent:
                parent_text += " " + (
                    parent.parent.get_text(
                        " ",
                        strip=True,
                    )
                )

        combined = (
            title + " " + parent_text
        ).strip()

        seen.add(full_url)

        results.append(
            {
                "url": full_url,
                "title": title,
                "listing_text": combined,
            }
        )

    return results


def looks_like_takeover_title(text):
    text = text.lower()

    return any(
        keyword in text
        for keyword in TAKEOVER_KEYWORDS
    )


def find_candidate_announcements(
    panel_candidates,
):
    """
    Scan recent RNS listings and match takeover-looking
    announcements against current Takeover Panel candidates.
    """

    matches = {}
    candidate_keys = []

    for candidate in panel_candidates:

        target = candidate.get(
            "target_name"
        )

        acquirer = candidate.get(
            "acquirer_name"
        )

        if not target:
            continue

        key = (
            normalize_name(target),
            normalize_name(acquirer),
        )

        candidate_keys.append(
            (
                key,
                target,
                acquirer,
            )
        )

    for page in range(
        1,
        MAX_RNS_PAGES + 1,
    ):

        print(
            f"Scanning recent RNS page {page}/"
            f"{MAX_RNS_PAGES}..."
        )

        try:
            rows = scrape_rns_listing_page(
                page
            )
        except Exception as exc:
            print(
                f"Could not scan RNS page "
                f"{page}: {exc}"
            )
            continue

        for row in rows:

            listing_text = row[
                "listing_text"
            ]

            if not looks_like_takeover_title(
                listing_text
            ):
                continue

            for (
                key,
                target,
                acquirer,
            ) in candidate_keys:

                if company_matches(
                    target,
                    listing_text,
                ):

                    url = row["url"]

                    if url not in matches:
                        matches[url] = {
                            "url": url,
                            "title": (
                                row["title"]
                                or listing_text[:200]
                            ),
                            "target_hint": target,
                            "acquirer_hint": acquirer,
                            "source_domain": (
                                "investegate.co.uk"
                            ),
                        }

                    break

        # Be polite to the public site.
        time.sleep(0.25)

    return list(matches.values())


# =========================================================
# ANNOUNCEMENT FETCHING
# =========================================================

def fetch_announcement_text(url):
    r = requests.get(
        url,
        headers=HEADERS,
        timeout=REQUEST_TIMEOUT,
    )

    r.raise_for_status()

    soup = BeautifulSoup(
        r.text,
        "html.parser",
    )

    # Strip layout/noise.
    for element in soup(
        [
            "script",
            "style",
            "nav",
            "footer",
            "header",
            "aside",
        ]
    ):
        element.decompose()

    text = soup.get_text(
        "\n",
        strip=True,
    )

    text = re.sub(
        r"\n{3,}",
        "\n\n",
        text,
    )

    # Protect against accidentally sending enormous pages.
    if len(text) > 100000:
        text = text[:100000]

    if len(text) < 300:
        raise ValueError(
            "Announcement text was unexpectedly short."
        )

    return text


# =========================================================
# GEMINI EXTRACTION
# =========================================================

def extract_deal(
    source_text,
    target_hint=None,
    acquirer_hint=None,
):
    prompt = f"""
You are the structured-data extraction engine for
UK Deal Pulse, a UK public M&A intelligence database.

Your task is factual extraction only.

SOURCE RULE

Use ONLY the supplied announcement text.

Do not rely on outside knowledge.

If a field is unsupported, return null.

Never guess.

Never invent missing deal values, advisers, premiums,
financing, countries, offer prices or rationale.

CANDIDATE HINTS

The Takeover Panel discovery stage suggests:

Possible target:
{target_hint}

Possible offeror:
{acquirer_hint}

These are ONLY hints.

The announcement itself is authoritative.

If the announcement contradicts the hints, use the
announcement.

ELIGIBILITY

The announcement must clearly concern an acquisition,
takeover, merger, firm offer, recommended offer or
completed acquisition involving the target.

Do NOT treat:

- rumours
- Rule 8 dealing disclosures
- ordinary shareholding notifications
- speculative press reports
- vague expressions of interest
- routine corporate announcements

as confirmed transactions.

DATE

announcement_date MUST be:

YYYY-MM-DD

MONEY

deal_value_gbp:

Use ONLY a GBP equity/deal value explicitly stated
in the announcement.

Return the full number.

Example:

£1.25 billion -> 1250000000

Do NOT convert currencies yourself.

PREMIUM

Only use a premium percentage explicitly stated.

Do NOT calculate one.

OFFER PRICE

Use the explicitly stated per-share offer value.

Examples of currency codes:

GBP
GBp
USD
EUR

BUYER TYPE

Return only:

Strategic
Private Equity
null

OFFER TYPE

Return only:

Cash
Shares
Mixed
Other
null

STATUS

Return only:

Announced
Recommended
Completed
Withdrawn
Other

ADVISERS

Only populate an adviser if the announcement clearly
identifies:

1. the adviser; and
2. which side the adviser represents.

Otherwise return null.

STRATEGIC RATIONALE

Maximum 65 words.

Use only rationale explicitly stated in the source.

CONFIDENCE

confidence MUST be a decimal number from 0 to 1.

Use confidence for confidence that:

- this is a genuine relevant transaction; and
- the core transaction identity is extracted correctly.

Never return:
High
Medium
Low

Return valid JSON ONLY with exactly these fields:

is_relevant_transaction
target_name
acquirer_name
announcement_date
deal_value_gbp
sector
buyer_type
acquirer_country
offer_type
offer_price
offer_price_currency
premium_percent
buyer_advisers
target_advisers
status
financing
strategic_rationale
confidence
uncertain_fields

SOURCE ANNOUNCEMENT:

{source_text}
"""

    for attempt in range(5):

        try:
            response = (
                client.models.generate_content(
                    model=GEMINI_MODEL,
                    contents=prompt,
                    config={
                        "response_mime_type":
                        "application/json"
                    },
                )
            )

            return json.loads(
                response.text
            )

        except errors.ServerError:

            if attempt == 4:
                raise

            wait_seconds = (
                10 * (attempt + 1)
            )

            print(
                "Gemini unavailable. "
                f"Retrying in "
                f"{wait_seconds}s..."
            )

            time.sleep(
                wait_seconds
            )

    raise RuntimeError(
        "Gemini did not return a response."
    )


# =========================================================
# VALIDATION
# =========================================================

def validate(deal):

    if (
        deal.get(
            "is_relevant_transaction"
        )
        is not True
    ):
        raise ValueError(
            "Not a relevant confirmed transaction."
        )

    required = [
        "target_name",
        "acquirer_name",
        "announcement_date",
        "confidence",
    ]

    for field in required:
        if deal.get(field) is None:
            raise ValueError(
                f"Missing required field: "
                f"{field}"
            )

    try:
        datetime.strptime(
            deal["announcement_date"],
            "%Y-%m-%d",
        )
    except ValueError:
        raise ValueError(
            "announcement_date must use "
            "YYYY-MM-DD"
        )

    confidence = float(
        deal["confidence"]
    )

    if not 0 <= confidence <= 1:
        raise ValueError(
            "confidence must be between "
            "0 and 1"
        )

    allowed_buyer_types = {
        "Strategic",
        "Private Equity",
        None,
    }

    allowed_offer_types = {
        "Cash",
        "Shares",
        "Mixed",
        "Other",
        None,
    }

    allowed_statuses = {
        "Announced",
        "Recommended",
        "Completed",
        "Withdrawn",
        "Other",
    }

    if (
        deal.get("buyer_type")
        not in allowed_buyer_types
    ):
        raise ValueError(
            "Invalid buyer_type"
        )

    if (
        deal.get("offer_type")
        not in allowed_offer_types
    ):
        raise ValueError(
            "Invalid offer_type"
        )

    if (
        deal.get("status")
        not in allowed_statuses
    ):
        raise ValueError(
            "Invalid status"
        )

    return confidence


# =========================================================
# DUPLICATES
# =========================================================

def duplicate_exists(
    deal,
    source_url,
):

    # Exact source URL.
    r = requests.get(
        f"{SUPABASE_URL}/rest/v1/deals",
        headers=db_headers(),
        params={
            "select": "id",
            "source_url":
            f"eq.{source_url}",
            "limit": "1",
        },
        timeout=REQUEST_TIMEOUT,
    )

    r.raise_for_status()

    if r.json():
        return True

    # Exact extracted transaction identity.
    r = requests.get(
        f"{SUPABASE_URL}/rest/v1/deals",
        headers=db_headers(),
        params={
            "select": "id",
            "target_name":
            f"eq.{deal['target_name']}",
            "acquirer_name":
            f"eq.{deal['acquirer_name']}",
            "announcement_date":
            (
                f"eq."
                f"{deal['announcement_date']}"
            ),
            "limit": "1",
        },
        timeout=REQUEST_TIMEOUT,
    )

    r.raise_for_status()

    return bool(r.json())


# =========================================================
# INSERT
# =========================================================

def insert_deal(
    deal,
    source_url,
    source_title,
):

    confidence = float(
        deal["confidence"]
    )

    uncertain_fields = (
        deal.get("uncertain_fields")
        or []
    )

    core_uncertainty = any(
        field in uncertain_fields
        for field in [
            "target_name",
            "acquirer_name",
            "announcement_date",
        ]
    )

    auto_publish = (
        confidence >= 0.92
        and not core_uncertainty
    )

    payload = {
        "target_name":
        deal.get("target_name"),

        "acquirer_name":
        deal.get("acquirer_name"),

        "announcement_date":
        deal.get("announcement_date"),

        "deal_value_gbp":
        deal.get("deal_value_gbp"),

        "sector":
        deal.get("sector"),

        "buyer_type":
        deal.get("buyer_type"),

        "acquirer_country":
        deal.get("acquirer_country"),

        "offer_type":
        deal.get("offer_type"),

        "offer_price":
        deal.get("offer_price"),

        "offer_price_currency":
        deal.get(
            "offer_price_currency"
        ),

        "premium_percent":
        deal.get("premium_percent"),

        "buyer_advisers":
        deal.get("buyer_advisers"),

        "target_advisers":
        deal.get("target_advisers"),

        "status":
        deal.get("status"),

        "financing":
        deal.get("financing"),

        "strategic_rationale":
        deal.get(
            "strategic_rationale"
        ),

        "source_url":
        source_url,

        "source_title":
        source_title,

        "source_domain":
        "investegate.co.uk",

        "ai_confidence":
        confidence,

        "verified":
        auto_publish,

        "auto_publish_eligible":
        auto_publish,
    }

    r = requests.post(
        f"{SUPABASE_URL}/rest/v1/deals",
        headers={
            **db_headers(),
            "Prefer":
            "return=representation",
        },
        json=payload,
        timeout=REQUEST_TIMEOUT,
    )

    r.raise_for_status()

    return r.json()


# =========================================================
# MAIN
# =========================================================

def main():

    print(
        "UK Deal Pulse weekly update"
    )

    print(
        "Discovering current Takeover "
        "Panel offer periods..."
    )

    panel_candidates = (
        discover_candidates()
    )

    print(
        f"Panel candidates: "
        f"{len(panel_candidates)}"
    )

    print(
        "Searching recent regulatory "
        "announcements..."
    )

    announcements = (
        find_candidate_announcements(
            panel_candidates
        )
    )

    print(
        f"Potential matching announcements: "
        f"{len(announcements)}"
    )

    already_processed = 0
    inserted = 0
    unverified = 0
    duplicates = 0
    rejected = 0
    errors_count = 0

    for item in announcements:

        url = item["url"]
        title = item["title"]

        print()
        print("=" * 70)
        print(
            f"Processing: {title}"
        )
        print(
            f"Target hint: "
            f"{item['target_hint']}"
        )
        print("=" * 70)

        try:

            if source_already_processed(
                url
            ):
                print(
                    "Already processed."
                )

                already_processed += 1
                continue

            print(
                "Fetching announcement..."
            )

            source_text = (
                fetch_announcement_text(
                    url
                )
            )

            print(
                "Extracting with Gemini..."
            )

            deal = extract_deal(
                source_text,
                item["target_hint"],
                item["acquirer_hint"],
            )

            print("EXTRACTED:")
            print(
                json.dumps(
                    deal,
                    indent=2,
                )
            )

            try:
                confidence = validate(
                    deal
                )
            except ValueError as exc:

                print(
                    f"Rejected: {exc}"
                )

                mark_processed(
                    url,
                    title,
                    "rejected",
                    str(exc),
                )

                rejected += 1
                continue

            if duplicate_exists(
                deal,
                url,
            ):

                print(
                    "Duplicate transaction."
                )

                mark_processed(
                    url,
                    title,
                    "duplicate",
                )

                duplicates += 1
                continue

            if confidence < 0.75:

                print(
                    "Rejected: low confidence."
                )

                mark_processed(
                    url,
                    title,
                    "rejected_low_confidence",
                )

                rejected += 1
                continue

            result = insert_deal(
                deal,
                url,
                title,
            )

            was_verified = bool(
                result
                and result[0].get(
                    "verified"
                )
            )

            if was_verified:
                inserted += 1

                print(
                    "INSERT SUCCESS — "
                    "published."
                )
            else:
                unverified += 1

                print(
                    "INSERT SUCCESS — "
                    "stored for review but "
                    "not published."
                )

            mark_processed(
                url,
                title,
                "inserted",
            )

        except Exception as exc:

            errors_count += 1

            print(
                f"ERROR: {exc}"
            )

            try:
                mark_processed(
                    url,
                    title,
                    "error",
                    str(exc)[:1000],
                )
            except Exception as log_exc:
                print(
                    "Could not write error "
                    f"log: {log_exc}"
                )

    print()
    print("=" * 70)
    print(
        "UK DEAL PULSE WEEKLY SUMMARY"
    )
    print("=" * 70)

    print(
        f"Panel candidates: "
        f"{len(panel_candidates)}"
    )

    print(
        f"Potential announcements: "
        f"{len(announcements)}"
    )

    print(
        f"Already processed: "
        f"{already_processed}"
    )

    print(
        f"Published: {inserted}"
    )

    print(
        f"Stored unverified: "
        f"{unverified}"
    )

    print(
        f"Duplicates: {duplicates}"
    )

    print(
        f"Rejected: {rejected}"
    )

    print(
        f"Errors: {errors_count}"
    )


if __name__ == "__main__":
    main()
