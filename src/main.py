import os
import re
import json
import time
from datetime import datetime, timezone

import requests
from bs4 import BeautifulSoup
from google import genai
from google.genai import errors

from discovery import discover_candidates
from rns_discovery import get_daily_takeover_rns


# =========================================================
# CONFIG
# =========================================================

GEMINI_API_KEY = os.environ["GEMINI_API_KEY"]
SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_KEY = os.environ["SUPABASE_SERVICE_ROLE_KEY"]

GEMINI_MODEL = "gemini-3.5-flash-lite"

REQUEST_TIMEOUT = 30

HTTP_HEADERS = {
    "User-Agent": "UKDealPulse/1.0"
}

client = genai.Client(api_key=GEMINI_API_KEY)


# =========================================================
# OFFICIAL ANNOUNCEMENT SOURCES
#
# These must be issuer / offeror / official regulatory sources.
# Never add Investegate URLs here.
#
# This list remains for historical / manually verified sources.
# New daily RNS discovery is handled separately below.
# =========================================================

OFFICIAL_SOURCES = [
    {
        "title": "Prologis Announces Recommended Acquisition of SEGRO plc",
        "url": (
            "https://ir.prologis.com/news-events/"
            "press-releases/detail/1049/"
            "prologis-announces-recommended-acquisition-of-segro-plc"
        ),
        "target_hint": "SEGRO plc",
        "acquirer_hint": "Prologis, Inc.",
        "source_domain": "ir.prologis.com",
    }
]


# =========================================================
# SUPABASE
# =========================================================

def db_headers():
    return {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
    }


def slugify(value):
    value = value.lower()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    return value.strip("-")


# =========================================================
# TAKEOVER PANEL CANDIDATE TRACKING
# =========================================================

def panel_candidate_key(target, acquirer):
    return (
        "takeover-panel://"
        + slugify(target)
        + "/"
        + slugify(acquirer)
    )


def processed_source(url):
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
        return None

    return rows[0]


def save_panel_candidate(target, acquirer):
    key = panel_candidate_key(target, acquirer)

    if processed_source(key):
        return False

    payload = {
        "source_url": key,
        "source_title": f"{target} <- {acquirer}",
        "discovered_at": datetime.now(timezone.utc).isoformat(),
        "processed_at": None,
        "processing_status": "discovered_candidate",
        "error_message": None,
    }

    r = requests.post(
        f"{SUPABASE_URL}/rest/v1/processed_sources",
        headers={
            **db_headers(),
            "Prefer": "return=minimal",
        },
        json=payload,
        timeout=REQUEST_TIMEOUT,
    )

    r.raise_for_status()
    return True


def mark_source(
    url,
    title,
    status,
    error_message=None,
):
    payload = {
        "source_url": url,
        "source_title": title,
        "discovered_at": datetime.now(timezone.utc).isoformat(),
        "processed_at": datetime.now(timezone.utc).isoformat(),
        "processing_status": status,
        "error_message": error_message,
    }

    r = requests.post(
        (
            f"{SUPABASE_URL}/rest/v1/processed_sources"
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
# SOURCE FETCHING
# =========================================================

def fetch_source_text(url):
    r = requests.get(
        url,
        headers=HTTP_HEADERS,
        timeout=REQUEST_TIMEOUT,
    )

    r.raise_for_status()

    soup = BeautifulSoup(
        r.text,
        "html.parser",
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
        strip=True,
    )

    text = re.sub(
        r"\n{3,}",
        "\n\n",
        text,
    )

    if len(text) < 300:
        raise ValueError(
            "Official source returned too little text."
        )

    return text[:100000]


# =========================================================
# NAME VALIDATION
# =========================================================

LEGAL_WORDS = {
    "plc",
    "limited",
    "ltd",
    "inc",
    "incorporated",
    "company",
    "corp",
    "corporation",
}


def name_tokens(value):
    value = (value or "").lower()
    value = re.sub(r"[^a-z0-9 ]", " ", value)

    return {
        token
        for token in value.split()
        if token not in LEGAL_WORDS
        and len(token) >= 3
    }


def names_compatible(extracted, expected):
    a = name_tokens(extracted or "")
    b = name_tokens(expected or "")

    if not a or not b:
        return False

    overlap = a.intersection(b)

    return bool(overlap)


# =========================================================
# DAILY RNS / TAKEOVER PANEL MATCHING
# =========================================================

def match_rns_to_panel_candidates(
    rns_items,
    candidates,
):
    """
    Match likely takeover RNS headlines against the current
    Takeover Panel offer-situation list.

    This does NOT yet send the RNS into Gemini.

    It safely identifies likely candidate/source pairs first.
    """

    matches = []

    for item in rns_items:
        issuer = (
            (item.get("issuer") or {}).get("name") or ""
        )

        headline = item.get("headline") or ""

        issuer_tokens = name_tokens(issuer)
        headline_tokens = name_tokens(headline)

        for candidate in candidates:
            target = (
                candidate.get("target_name") or ""
            )

            acquirer = (
                candidate.get("acquirer_name") or ""
            )

            target_tokens = name_tokens(target)
            acquirer_tokens = name_tokens(acquirer)

            target_match = bool(
                target_tokens.intersection(
                    issuer_tokens.union(
                        headline_tokens
                    )
                )
            )

            acquirer_match = bool(
                acquirer_tokens.intersection(
                    headline_tokens
                )
            )

            if target_match or acquirer_match:
                matches.append({
                    "rns": item,
                    "target_hint": target,
                    "acquirer_hint": acquirer,
                })

                break

    return matches


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

This is a factual extraction task.

Use ONLY the supplied official source.

If information is unsupported, return null.

Never guess.
Never invent data.
Never calculate a takeover premium.
Never perform your own FX conversion.
Never assign an adviser unless its side is explicitly clear.

EXPECTED TRANSACTION HINTS

Possible target:
{target_hint}

Possible acquirer:
{acquirer_hint}

These are hints only.
The official source is authoritative.

TRANSACTION ELIGIBILITY

is_relevant_transaction must be true only if the source clearly concerns:
- a firm takeover/acquisition
- recommended offer
- scheme acquisition
- completed acquisition
- definitive merger transaction

Reject:
- rumours
- possible offers without a firm offer
- shareholding disclosures
- dealing disclosures
- unrelated corporate news

DATE

announcement_date must be YYYY-MM-DD.

MONEY

deal_value_gbp:
Use only a GBP transaction/equity value explicitly stated by the source.
Return the full integer amount.

Do not convert a foreign currency value into GBP yourself.

PREMIUM

premium_percent:
Only populate if explicitly stated by the source.

BUYER TYPE

Return exactly one of:
Strategic
Private Equity
null

OFFER TYPE

Return exactly one of:
Cash
Shares
Mixed
Other
null

STATUS

Return exactly one of:
Announced
Recommended
Completed
Withdrawn
Other

RATIONALE

strategic_rationale:
Maximum 65 words.
Source-supported only.

CONFIDENCE

confidence must be a decimal between 0 and 1.

Do not return High / Medium / Low.

Return JSON only with exactly:

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

OFFICIAL SOURCE:

{source_text}
"""

    for attempt in range(5):
        try:
            response = client.models.generate_content(
                model=GEMINI_MODEL,
                contents=prompt,
                config={
                    "response_mime_type": "application/json"
                },
            )

            return json.loads(response.text)

        except errors.ServerError:
            if attempt == 4:
                raise

            wait = 10 * (attempt + 1)

            print(
                f"Gemini unavailable. Retrying in {wait}s..."
            )

            time.sleep(wait)

    raise RuntimeError(
        "Gemini did not return a response."
    )


# =========================================================
# VALIDATION
# =========================================================

def validate(
    deal,
    target_hint,
    acquirer_hint,
):
    if deal.get("is_relevant_transaction") is not True:
        raise ValueError(
            "Source is not a confirmed relevant transaction."
        )

    required = [
        "target_name",
        "acquirer_name",
        "announcement_date",
        "confidence",
    ]

    for field in required:
        if not deal.get(field):
            raise ValueError(
                f"Missing required field: {field}"
            )

    try:
        datetime.strptime(
            deal["announcement_date"],
            "%Y-%m-%d",
        )

    except ValueError:
        raise ValueError(
            "announcement_date is not YYYY-MM-DD."
        )

    confidence = float(
        deal["confidence"]
    )

    if not 0 <= confidence <= 1:
        raise ValueError(
            "Invalid confidence."
        )

    if not names_compatible(
        deal["target_name"],
        target_hint,
    ):
        raise ValueError(
            "Extracted target does not match expected target."
        )

    if not names_compatible(
        deal["acquirer_name"],
        acquirer_hint,
    ):
        raise ValueError(
            "Extracted acquirer does not match expected acquirer."
        )

    return confidence


# =========================================================
# DEAL DUPLICATION
# =========================================================

def duplicate_deal(
    deal,
    source_url,
):
    r = requests.get(
        f"{SUPABASE_URL}/rest/v1/deals",
        headers=db_headers(),
        params={
            "select": "id",
            "source_url": f"eq.{source_url}",
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
            "target_name": (
                f"eq.{deal['target_name']}"
            ),
            "acquirer_name": (
                f"eq.{deal['acquirer_name']}"
            ),
            "announcement_date": (
                f"eq.{deal['announcement_date']}"
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
    source,
    confidence,
):
    uncertain = deal.get(
        "uncertain_fields"
    ) or []

    core_uncertain = any(
        x in uncertain
        for x in [
            "target_name",
            "acquirer_name",
            "announcement_date",
        ]
    )

    publish = (
        confidence >= 0.92
        and not core_uncertain
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
            deal.get("offer_price_currency"),

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
            deal.get("strategic_rationale"),

        "source_url":
            source["url"],

        "source_title":
            source["title"],

        "source_domain":
            source["source_domain"],

        "ai_confidence":
            confidence,

        "verified":
            publish,

        "auto_publish_eligible":
            publish,
    }

    r = requests.post(
        f"{SUPABASE_URL}/rest/v1/deals",
        headers={
            **db_headers(),
            "Prefer": "return=representation",
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
    print("=" * 70)
    print("UK DEAL PULSE DAILY UPDATE")
    print("=" * 70)

    # -----------------------------------------------------
    # 1. TAKEOVER PANEL DISCOVERY
    # -----------------------------------------------------

    candidates = discover_candidates()

    print(
        f"Current Takeover Panel candidates: "
        f"{len(candidates)}"
    )

    new_candidates = 0
    known_candidates = 0

    for candidate in candidates:

        target = candidate.get(
            "target_name"
        )

        acquirer = candidate.get(
            "acquirer_name"
        )

        if not target or not acquirer:
            continue

        if save_panel_candidate(
            target,
            acquirer,
        ):
            new_candidates += 1

            print(
                f"NEW: {target} <- {acquirer}"
            )

        else:
            known_candidates += 1

    # -----------------------------------------------------
    # 2. DAILY RNS DISCOVERY
    # -----------------------------------------------------

    print()
    print("-" * 70)
    print("DAILY RNS DISCOVERY")
    print("-" * 70)

    try:
        rns_items = get_daily_takeover_rns()

        print(
            f"Likely takeover RNS announcements: "
            f"{len(rns_items)}"
        )

        matched_rns = match_rns_to_panel_candidates(
            rns_items,
            candidates,
        )

        print(
            f"Matched to Takeover Panel candidates: "
            f"{len(matched_rns)}"
        )

        for match in matched_rns:
            item = match["rns"]

            print()
            print(
                "RNS MATCH:",
                match["target_hint"],
                "<-",
                match["acquirer_hint"],
            )

            print(
                "RNS ID:",
                item.get("rnsId"),
            )

            print(
                "Headline:",
                item.get("headline"),
            )

            print(
                "Issuer:",
                (item.get("issuer") or {}).get(
                    "name"
                ),
            )

    except Exception as exc:
        print(
            f"RNS DISCOVERY ERROR: {exc}"
        )

        rns_items = []
        matched_rns = []

    # -----------------------------------------------------
    # 3. OFFICIAL SOURCE INGESTION
    # -----------------------------------------------------

    published = 0
    unverified = 0
    duplicates = 0
    rejected = 0
    already_processed = 0
    errors_count = 0

    print()
    print(
        f"Official sources configured: "
        f"{len(OFFICIAL_SOURCES)}"
    )

    for source in OFFICIAL_SOURCES:

        print()
        print("-" * 70)
        print(
            f"Processing official source: "
            f"{source['title']}"
        )
        print("-" * 70)

        try:

            existing = processed_source(
                source["url"]
            )

            if existing and (
                existing.get(
                    "processing_status"
                )
                != "error"
            ):
                print(
                    "Source already processed."
                )

                already_processed += 1
                continue

            text = fetch_source_text(
                source["url"]
            )

            deal = extract_deal(
                text,
                source["target_hint"],
                source["acquirer_hint"],
            )

            print(
                json.dumps(
                    deal,
                    indent=2,
                )
            )

            confidence = validate(
                deal,
                source["target_hint"],
                source["acquirer_hint"],
            )

            if duplicate_deal(
                deal,
                source["url"],
            ):
                print(
                    "Duplicate transaction."
                )

                mark_source(
                    source["url"],
                    source["title"],
                    "duplicate",
                )

                duplicates += 1
                continue

            if confidence < 0.75:

                print(
                    "Rejected: low confidence."
                )

                mark_source(
                    source["url"],
                    source["title"],
                    "rejected_low_confidence",
                )

                rejected += 1
                continue

            rows = insert_deal(
                deal,
                source,
                confidence,
            )

            is_verified = bool(
                rows
                and rows[0].get(
                    "verified"
                )
            )

            if is_verified:
                published += 1

                print(
                    "INSERT SUCCESS — published"
                )

            else:
                unverified += 1

                print(
                    "INSERT SUCCESS — stored unverified"
                )

            mark_source(
                source["url"],
                source["title"],
                "inserted",
            )

        except Exception as exc:

            errors_count += 1

            print(
                f"ERROR: {exc}"
            )

            try:
                mark_source(
                    source["url"],
                    source["title"],
                    "error",
                    str(exc)[:1000],
                )

            except Exception:
                pass

    # -----------------------------------------------------
    # SUMMARY
    # -----------------------------------------------------

    print()
    print("=" * 70)
    print("UK DEAL PULSE DAILY SUMMARY")
    print("=" * 70)

    print(
        f"Current Panel candidates: "
        f"{len(candidates)}"
    )

    print(
        f"New Panel candidates: "
        f"{new_candidates}"
    )

    print(
        f"Already-known Panel candidates: "
        f"{known_candidates}"
    )

    print(
        f"Likely takeover RNS today: "
        f"{len(rns_items)}"
    )

    print(
        f"RNS matched to Panel candidates: "
        f"{len(matched_rns)}"
    )

    print(
        f"Official sources checked: "
        f"{len(OFFICIAL_SOURCES)}"
    )

    print(
        f"Already processed sources: "
        f"{already_processed}"
    )

    print(
        f"Published: {published}"
    )

    print(
        f"Stored unverified: {unverified}"
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
