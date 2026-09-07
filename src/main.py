import os
import json
import time
from datetime import datetime, timezone

import requests
from google import genai
from google.genai import errors


# =========================================================
# CONFIG
# =========================================================

GEMINI_API_KEY = os.environ["GEMINI_API_KEY"]
SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_KEY = os.environ["SUPABASE_SERVICE_ROLE_KEY"]

client = genai.Client(api_key=GEMINI_API_KEY)


# =========================================================
# TEST CANDIDATE
# Later, automatic discovery will replace this list.
# =========================================================

CANDIDATES = [
    {
        "title": "Recommended Cash Acquisition of Capricorn by DNO",
        "url": (
            "https://www.investegate.co.uk/announcement/rns/"
            "capricorn-energy--cne/recommended-cash-acquisition-of-"
            "capricorn-by-dno/9747188"
        ),
        "source_domain": "investegate.co.uk",
        "source_text": """
1 September 2026

Recommended cash acquisition of Capricorn Energy plc by DNO Bidco AS.

DNO Bidco AS is directly wholly owned by DNO ASA.

The boards of DNO, Bidco and Capricorn announced agreement on a
recommended cash acquisition of the entire issued and to be issued
ordinary share capital of Capricorn.

The transaction is intended to be implemented by a Scottish scheme of
arrangement under Part 26 of the Companies Act 2006.

Capricorn shareholders are entitled to an aggregate acquisition value
of US$5.214 per share.

This comprises US$4.224 in cash plus an intended special dividend of
US$0.99 per share.

The sterling equivalent acquisition value is approximately 384 pence
per Capricorn share.

The acquisition implies a fully diluted equity value of approximately
US$396 million, equivalent to approximately £292 million.

The sterling acquisition value represents an approximately 45 percent
premium to Capricorn's closing share price on 10 March 2026.

DNO is an oil and gas exploration and production company.

DNO views the acquisition as an entry into Egypt and intends to develop
Egypt as a third core operating area alongside the North Sea and the
Kurdistan Region of Iraq.

Capricorn's Egyptian assets and established team are viewed by DNO as
a platform for further investment and growth.
"""
    }
]


# =========================================================
# SUPABASE
# =========================================================

def headers():
    return {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
    }


def source_already_processed(url):
    r = requests.get(
        f"{SUPABASE_URL}/rest/v1/processed_sources",
        headers=headers(),
        params={
            "select": "id,processing_status",
            "source_url": f"eq.{url}",
            "limit": "1",
        },
        timeout=30,
    )

    r.raise_for_status()
    rows = r.json()

    if not rows:
        return False

    status = rows[0].get("processing_status")

    # Retry sources which previously failed.
    if status == "error":
        return False

    return True


def mark_processed(
    url,
    title,
    status,
    error_message=None,
):
    payload = {
        "source_url": url,
        "source_title": title,
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
            **headers(),
            "Prefer": "resolution=merge-duplicates,return=minimal",
        },
        json=payload,
        timeout=30,
    )

    r.raise_for_status()


# =========================================================
# GEMINI EXTRACTION
# =========================================================

def extract_deal(source_text):
    prompt = f"""
You are the structured-data extraction engine for UK Deal Pulse,
a database of UK public-company M&A transactions.

FACTUALITY RULES

Use ONLY the supplied source text.

If a field is not explicitly supported, return null.

Never guess.

Never invent advisers, financing, values, countries, sectors,
premiums or transaction terms.

Do not calculate a premium yourself.

Do not perform currency conversion yourself.

DATE FORMAT

announcement_date MUST use:
YYYY-MM-DD

CONFIDENCE FORMAT

confidence MUST be a decimal number from 0 to 1.

For example:

0.98

Never return:
"High"
"Medium"
"Low"

BUYER TYPE

Return only:

"Strategic"
"Private Equity"
null

OFFER TYPE

Return only:

"Cash"
"Shares"
"Mixed"
"Other"
null

STATUS

Return only:

"Announced"
"Recommended"
"Completed"
"Withdrawn"
"Other"

MONEY

deal_value_gbp should contain ONLY a GBP transaction/equity value
explicitly stated in the source.

Return it as a full number.

Example:
£292 million -> 292000000

offer_price should contain the stated per-share acquisition/offer value.

offer_price_currency should identify the currency clearly, for example:
"USD"
"GBP"
"GBp"

STRATEGIC RATIONALE

Maximum 65 words.

Only summarise rationale explicitly stated in the supplied source.

ADVISERS

Only populate buyer_advisers or target_advisers when the source
clearly identifies the adviser AND which side it advises.

Otherwise return null.

Return VALID JSON ONLY with exactly these fields:

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

SOURCE TEXT:

{source_text}
"""

    for attempt in range(5):
        try:
            response = client.models.generate_content(
                model="gemini-3.5-flash-lite",
                contents=prompt,
                config={
                    "response_mime_type": "application/json"
                },
            )

            return json.loads(response.text)

        except errors.ServerError:
            if attempt == 4:
                raise

            wait_seconds = 10 * (attempt + 1)

            print(
                "Gemini temporarily unavailable. "
                f"Retrying in {wait_seconds}s..."
            )

            time.sleep(wait_seconds)

    raise RuntimeError("Gemini failed to return a response.")


# =========================================================
# VALIDATION
# =========================================================

def validate(deal):
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

    # Validate ISO date.
    try:
        datetime.strptime(
            deal["announcement_date"],
            "%Y-%m-%d"
        )
    except ValueError:
        raise ValueError(
            "announcement_date must be YYYY-MM-DD"
        )

    confidence = float(deal["confidence"])

    if confidence < 0 or confidence > 1:
        raise ValueError(
            "confidence must be between 0 and 1"
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

    if deal.get("buyer_type") not in allowed_buyer_types:
        raise ValueError("Invalid buyer_type")

    if deal.get("offer_type") not in allowed_offer_types:
        raise ValueError("Invalid offer_type")

    if deal.get("status") not in allowed_statuses:
        raise ValueError("Invalid status")

    return confidence


# =========================================================
# DEDUPLICATION
# =========================================================

def duplicate_exists(deal, source_url):

    # Check exact source URL first.
    r = requests.get(
        f"{SUPABASE_URL}/rest/v1/deals",
        headers=headers(),
        params={
            "select": "id",
            "source_url": f"eq.{source_url}",
            "limit": "1",
        },
        timeout=30,
    )

    r.raise_for_status()

    if r.json():
        return True

    # Then check transaction identity.
    r = requests.get(
        f"{SUPABASE_URL}/rest/v1/deals",
        headers=headers(),
        params={
            "select": "id",
            "target_name": f"eq.{deal['target_name']}",
            "acquirer_name": f"eq.{deal['acquirer_name']}",
            "announcement_date": (
                f"eq.{deal['announcement_date']}"
            ),
            "limit": "1",
        },
        timeout=30,
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
    source_domain,
):
    confidence = float(deal["confidence"])

    # High confidence is eligible for automatic publication.
    auto_publish = confidence >= 0.92

    payload = {
        "target_name": deal.get("target_name"),
        "acquirer_name": deal.get("acquirer_name"),
        "announcement_date": deal.get(
            "announcement_date"
        ),
        "deal_value_gbp": deal.get("deal_value_gbp"),
        "sector": deal.get("sector"),
        "buyer_type": deal.get("buyer_type"),
        "acquirer_country": deal.get(
            "acquirer_country"
        ),
        "offer_type": deal.get("offer_type"),
        "offer_price": deal.get("offer_price"),
        "offer_price_currency": deal.get(
            "offer_price_currency"
        ),
        "premium_percent": deal.get(
            "premium_percent"
        ),
        "buyer_advisers": deal.get(
            "buyer_advisers"
        ),
        "target_advisers": deal.get(
            "target_advisers"
        ),
        "status": deal.get("status"),
        "financing": deal.get("financing"),
        "strategic_rationale": deal.get(
            "strategic_rationale"
        ),
        "source_url": source_url,
        "source_title": source_title,
        "source_domain": source_domain,
        "ai_confidence": confidence,
        "verified": auto_publish,
        "auto_publish_eligible": auto_publish,
    }

    r = requests.post(
        f"{SUPABASE_URL}/rest/v1/deals",
        headers={
            **headers(),
            "Prefer": "return=representation",
        },
        json=payload,
        timeout=30,
    )

    r.raise_for_status()

    return r.json()


# =========================================================
# MAIN PIPELINE
# =========================================================

def main():

    inserted = 0
    duplicates = 0
    rejected = 0
    errors_count = 0

    print(
        f"Found {len(CANDIDATES)} candidate announcement(s)"
    )

    for item in CANDIDATES:

        url = item["url"]
        title = item["title"]
        domain = item["source_domain"]

        print()
        print("=" * 60)
        print(f"Processing: {title}")
        print("=" * 60)

        try:

            if source_already_processed(url):
                print("Already processed — skipping.")
                duplicates += 1
                continue

            print("Extracting with Gemini...")

            deal = extract_deal(
                item["source_text"]
            )

            print("EXTRACTED:")
            print(
                json.dumps(
                    deal,
                    indent=2
                )
            )

            confidence = validate(deal)

            print(
                f"Validation passed. "
                f"Confidence: {confidence}"
            )

            if duplicate_exists(deal, url):

                print(
                    "Duplicate transaction detected."
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
                    "Rejected: confidence below 0.75"
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
                title,
                domain,
            )

            mark_processed(
                url,
                title,
                "inserted"
            )

            inserted += 1

            print("INSERT SUCCESS")

            print(
                json.dumps(
                    result,
                    indent=2
                )
            )

            if confidence >= 0.92:
                print(
                    "Deal automatically published "
                    "(verified = true)."
                )
            else:
                print(
                    "Deal stored but not publicly "
                    "published (verified = false)."
                )

        except Exception as e:

            errors_count += 1

            print(
                f"ERROR processing {title}: {e}"
            )

            try:
                mark_processed(
                    url,
                    title,
                    "error",
                    str(e)[:1000],
                )
            except Exception as log_error:
                print(
                    "Could not record processing "
                    f"error: {log_error}"
                )

    print()
    print("=" * 60)
    print("UK DEAL PULSE INGESTION SUMMARY")
    print("=" * 60)

    print(f"Candidates: {len(CANDIDATES)}")
    print(f"Inserted: {inserted}")
    print(f"Duplicates/skipped: {duplicates}")
    print(f"Rejected: {rejected}")
    print(f"Errors: {errors_count}")


if __name__ == "__main__":
    main()
