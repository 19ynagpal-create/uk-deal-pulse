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


GEMINI_API_KEY = os.environ["GEMINI_API_KEY"]
SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_KEY = os.environ["SUPABASE_SERVICE_ROLE_KEY"]

GEMINI_MODEL = "gemini-3.5-flash-lite"

INVESTEGATE_BASE = "https://www.investegate.co.uk"
INVESTEGATE_RNS = "https://www.investegate.co.uk/source/RNS"

MAX_RNS_PAGES = 25
REQUEST_TIMEOUT = 30

HEADERS = {
    "User-Agent": "UKDealPulse/1.0"
}

client = genai.Client(api_key=GEMINI_API_KEY)


# =========================================================
# DB
# =========================================================

def db_headers():
    return {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
    }


# =========================================================
# NAME MATCHING
# =========================================================

GENERIC_COMPANY_WORDS = {
    "plc",
    "limited",
    "ltd",
    "inc",
    "incorporated",
    "company",
    "group",
    "holdings",
    "holding",
    "energy",
    "international",
    "global",
    "capital",
    "resources",
    "investment",
    "investments",
}


def normalize_words(value):
    if not value:
        return []

    value = value.lower()
    value = re.sub(r"[^a-z0-9 ]", " ", value)
    value = re.sub(r"\s+", " ", value).strip()

    return [
        word
        for word in value.split()
        if word not in GENERIC_COMPANY_WORDS
        and len(word) >= 3
    ]


def target_matches(target_name, listing_text):
    """
    Strict matching:
    require at least one distinctive target token,
    and for multi-word distinctive names require most of them.
    """

    target_words = normalize_words(target_name)
    listing_words = set(normalize_words(listing_text))

    if not target_words:
        return False

    matches = [
        word
        for word in target_words
        if word in listing_words
    ]

    if len(target_words) == 1:
        return len(matches) == 1

    required = max(
        2,
        int(len(target_words) * 0.75)
    )

    return len(matches) >= required


# =========================================================
# OBVIOUS NON-DEAL ANNOUNCEMENTS
# =========================================================

REJECT_TITLE_PATTERNS = (
    "form 8.3",
    "form 8.5",
    "form 38.5",
    "form 8 ",
    "opening position disclosure",
    "dealing disclosure",
    "irish takeover panel",
    "rule 8",
    "rule 38",
    "notification of major holdings",
    "holding(s) in company",
    "director dealing",
    "transaction in own shares",
)


POSITIVE_TITLE_PATTERNS = (
    "recommended cash acquisition",
    "recommended acquisition",
    "recommended offer",
    "firm offer",
    "cash offer",
    "offer for",
    "acquisition of",
    "scheme of arrangement",
    "final recommended cash offer",
    "revised recommended cash offer",
    "rule 2.7",
)


def is_obvious_non_deal(text):
    lower = text.lower()

    return any(
        pattern in lower
        for pattern in REJECT_TITLE_PATTERNS
    )


def looks_like_real_takeover_announcement(text):
    lower = text.lower()

    if is_obvious_non_deal(lower):
        return False

    return any(
        pattern in lower
        for pattern in POSITIVE_TITLE_PATTERNS
    )


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

    return rows[0].get("processing_status") != "error"


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
# INVESTEGATE LISTINGS
# =========================================================

def scrape_rns_listing_page(page_number):
    url = f"{INVESTEGATE_RNS}?page={page_number}"

    r = requests.get(
        url,
        headers=HEADERS,
        timeout=REQUEST_TIMEOUT,
    )
    r.raise_for_status()

    soup = BeautifulSoup(
        r.text,
        "html.parser"
    )

    results = []
    seen = set()

    for link in soup.find_all("a", href=True):
        href = link.get("href", "")

        if "/announcement/" not in href:
            continue

        full_url = urljoin(
            INVESTEGATE_BASE,
            href
        )

        if full_url in seen:
            continue

        title = link.get_text(
            " ",
            strip=True
        )

        context_parts = [title]

        parent = link.parent

        # Pull a little row context, but not huge page chunks.
        for _ in range(3):
            if not parent:
                break

            text = parent.get_text(
                " ",
                strip=True
            )

            if text and len(text) < 1000:
                context_parts.append(text)

            parent = parent.parent

        listing_text = " ".join(
            dict.fromkeys(context_parts)
        )

        seen.add(full_url)

        results.append({
            "url": full_url,
            "title": title,
            "listing_text": listing_text,
        })

    return results


def find_candidate_announcements(panel_candidates):
    matches = {}

    for page in range(
        1,
        MAX_RNS_PAGES + 1
    ):
        print(
            f"Scanning RNS page "
            f"{page}/{MAX_RNS_PAGES}..."
        )

        try:
            rows = scrape_rns_listing_page(
                page
            )
        except Exception as exc:
            print(
                f"Could not scan page {page}: {exc}"
            )
            continue

        for row in rows:
            listing_text = row["listing_text"]
            title = row["title"]

            # Reject obvious Rule 8 / dealing disclosure noise.
            if is_obvious_non_deal(
                title + " " + listing_text
            ):
                continue

            # Only consider titles which look like actual offer announcements.
            if not looks_like_real_takeover_announcement(
                title + " " + listing_text
            ):
                continue

            for candidate in panel_candidates:
                target = candidate.get(
                    "target_name"
                )
                acquirer = candidate.get(
                    "acquirer_name"
                )

                if not target:
                    continue

                if not target_matches(
                    target,
                    listing_text
                ):
                    continue

                matches[row["url"]] = {
                    "url": row["url"],
                    "title": title,
                    "target_hint": target,
                    "acquirer_hint": acquirer,
                }

                break

        time.sleep(0.25)

    return list(matches.values())


# =========================================================
# FETCH FULL ANNOUNCEMENT
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
        "html.parser"
    )

    for element in soup([
        "script",
        "style",
        "nav",
        "footer",
        "header",
        "aside",
    ]):
        element.decompose()

    text = soup.get_text(
        "\n",
        strip=True
    )

    text = re.sub(
        r"\n{3,}",
        "\n\n",
        text
    )

    if len(text) > 100000:
        text = text[:100000]

    if len(text) < 300:
        raise ValueError(
            "Announcement text too short"
        )

    return text


# =========================================================
# GEMINI
# =========================================================

def extract_deal(
    source_text,
    target_hint,
    acquirer_hint,
):
    prompt = f"""
You are the structured-data extraction engine for UK Deal Pulse.

Use ONLY the supplied source announcement.

If a fact is unsupported, return null.

Never guess.
Never infer missing advisers.
Never calculate premiums.
Never convert currencies yourself.

The Takeover Panel discovery stage suggests:

Target:
{target_hint}

Offeror:
{acquirer_hint}

These are only hints.
The announcement itself is authoritative.

A relevant transaction must clearly be:
- an acquisition
- takeover
- firm offer
- recommended offer
- scheme acquisition
- completed acquisition

Reject:
- Form 8.3
- Form 8.5
- Form 38.5
- dealing disclosures
- opening position disclosures
- shareholding notifications
- rumours
- speculative reports

announcement_date must be YYYY-MM-DD.

confidence must be a decimal number between 0 and 1.

buyer_type:
Strategic
Private Equity
null

offer_type:
Cash
Shares
Mixed
Other
null

status:
Announced
Recommended
Completed
Withdrawn
Other

deal_value_gbp:
only use an explicitly stated GBP deal/equity value.
Return full integer number.

premium_percent:
only use an explicitly stated premium.

buyer_advisers / target_advisers:
only populate when adviser side is explicit.

strategic_rationale:
maximum 65 words and source-grounded only.

Return valid JSON only:

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

SOURCE:

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

            wait = 10 * (
                attempt + 1
            )

            print(
                f"Gemini unavailable. "
                f"Retrying in {wait}s..."
            )

            time.sleep(wait)

    raise RuntimeError(
        "Gemini failed"
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
            "Not a relevant confirmed transaction"
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
                f"Missing required field: {field}"
            )

    datetime.strptime(
        deal["announcement_date"],
        "%Y-%m-%d"
    )

    confidence = float(
        deal["confidence"]
    )

    if not 0 <= confidence <= 1:
        raise ValueError(
            "Invalid confidence"
        )

    return confidence


# =========================================================
# DUPLICATE CHECK
# =========================================================

def duplicate_exists(
    deal,
    source_url,
):
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
            f"eq.{deal['announcement_date']}",
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

    panel_candidates = (
        discover_candidates()
    )

    print(
        f"Panel candidates: "
        f"{len(panel_candidates)}"
    )

    announcements = (
        find_candidate_announcements(
            panel_candidates
        )
    )

    print(
        f"Potential announcements: "
        f"{len(announcements)}"
    )

    already_processed = 0
    published = 0
    stored_unverified = 0
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
                    "Already processed"
                )
                already_processed += 1
                continue

            source_text = (
                fetch_announcement_text(
                    url
                )
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
                    indent=2
                )
            )

            try:
                confidence = validate(
                    deal
                )
            except Exception as exc:
                print(
                    f"Rejected: {exc}"
                )

                mark_processed(
                    url,
                    title,
                    "rejected",
                    str(exc)
                )

                rejected += 1
                continue

            if duplicate_exists(
                deal,
                url
            ):
                print(
                    "Duplicate transaction"
                )

                mark_processed(
                    url,
                    title,
                    "duplicate"
                )

                duplicates += 1
                continue

            if confidence < 0.75:
                print(
                    "Rejected: low confidence"
                )

                mark_processed(
                    url,
                    title,
                    "rejected_low_confidence"
                )

                rejected += 1
                continue

            result = insert_deal(
                deal,
                url,
                title
            )

            is_verified = bool(
                result
                and result[0].get(
                    "verified"
                )
            )

            if is_verified:
                published += 1
                print(
                    "INSERT SUCCESS — published"
                )
            else:
                stored_unverified += 1
                print(
                    "INSERT SUCCESS — unverified"
                )

            mark_processed(
                url,
                title,
                "inserted"
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
                    str(exc)[:1000]
                )
            except Exception:
                pass

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
        f"Published: {published}"
    )
    print(
        f"Stored unverified: "
        f"{stored_unverified}"
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
