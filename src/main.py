import os
import json
import time
import requests

from google import genai
from google.genai import errors

GEMINI_API_KEY = os.environ["GEMINI_API_KEY"]
SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_KEY = os.environ["SUPABASE_SERVICE_ROLE_KEY"]

client = genai.Client(api_key=GEMINI_API_KEY)

# TEMPORARY FIRST VERSION:
# We will replace this list with automatic source discovery next.
CANDIDATES = [
    {
        "title": "Example UK M&A announcement",
        "url": "PASTE_A_NEW_ANNOUNCEMENT_URL_HERE",
        "source_text": """
PASTE THE ANNOUNCEMENT TEXT HERE
"""
    }
]


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
            "select": "id",
            "source_url": f"eq.{url}",
            "limit": "1",
        },
        timeout=30,
    )
    r.raise_for_status()
    return bool(r.json())


def mark_processed(url, title, status, error_message=None):
    payload = {
        "source_url": url,
        "source_title": title,
        "processing_status": status,
        "error_message": error_message,
    }

    requests.post(
        f"{SUPABASE_URL}/rest/v1/processed_sources",
        headers={
            **headers(),
            "Prefer": "resolution=merge-duplicates",
        },
        json=payload,
        timeout=30,
    )


def extract_deal(source_text):
    prompt = f"""
You are the structured-data extraction engine for UK Deal Pulse.

Use only the source text provided.

Rules:
- If unsupported, return null.
- Never guess.
- Never calculate a premium unless explicitly stated.
- announcement_date must be YYYY-MM-DD.
- confidence must be a decimal from 0 to 1.

Return valid JSON only with:

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

Allowed buyer_type:
Strategic
Private Equity
null

Allowed status:
Announced
Recommended
Completed
Withdrawn
Other

Allowed offer_type:
Cash
Shares
Mixed
Other
null

Source:
{source_text}
"""

    for attempt in range(5):
        try:
            response = client.models.generate_content(
                model="gemini-3.5-flash-lite",
                contents=prompt,
                config={"response_mime_type": "application/json"},
            )
            return json.loads(response.text)

        except errors.ServerError:
            if attempt == 4:
                raise

            wait = 10 * (attempt + 1)
            print(f"Gemini unavailable. Retrying in {wait}s...")
            time.sleep(wait)


def validate(deal):
    required = [
        "target_name",
        "acquirer_name",
        "announcement_date",
        "confidence",
    ]

    for field in required:
        if deal.get(field) is None:
            raise ValueError(f"Missing required field: {field}")

    confidence = float(deal["confidence"])

    return confidence


def duplicate_exists(deal, source_url):
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

    r = requests.get(
        f"{SUPABASE_URL}/rest/v1/deals",
        headers=headers(),
        params={
            "select": "id",
            "target_name": f"eq.{deal['target_name']}",
            "acquirer_name": f"eq.{deal['acquirer_name']}",
            "announcement_date": f"eq.{deal['announcement_date']}",
            "limit": "1",
        },
        timeout=30,
    )
    r.raise_for_status()

    return bool(r.json())


def insert_deal(deal, source_url, source_title):
    confidence = float(deal["confidence"])

    payload = {
        "target_name": deal.get("target_name"),
        "acquirer_name": deal.get("acquirer_name"),
        "announcement_date": deal.get("announcement_date"),
        "deal_value_gbp": deal.get("deal_value_gbp"),
        "sector": deal.get("sector"),
        "buyer_type": deal.get("buyer_type"),
        "acquirer_country": deal.get("acquirer_country"),
        "offer_type": deal.get("offer_type"),
        "offer_price": deal.get("offer_price"),
        "offer_price_currency": deal.get("offer_price_currency"),
        "premium_percent": deal.get("premium_percent"),
        "buyer_advisers": deal.get("buyer_advisers"),
        "target_advisers": deal.get("target_advisers"),
        "status": deal.get("status"),
        "financing": deal.get("financing"),
        "strategic_rationale": deal.get("strategic_rationale"),
        "source_url": source_url,
        "source_title": source_title,
        "ai_confidence": confidence,
        "verified": confidence >= 0.92,
        "auto_publish_eligible": confidence >= 0.92,
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


def main():
    inserted = 0
    skipped = 0
    errors_count = 0

    for item in CANDIDATES:
        url = item["url"]
        title = item["title"]

        try:
            if source_already_processed(url):
                print(f"Already processed: {title}")
                skipped += 1
                continue

            deal = extract_deal(item["source_text"])

            print(f"Extracted: {deal}")

            confidence = validate(deal)

            if duplicate_exists(deal, url):
                print(f"Duplicate: {title}")
                mark_processed(url, title, "duplicate")
                skipped += 1
                continue

            if confidence < 0.75:
                print(f"Rejected low confidence: {title}")
                mark_processed(url, title, "rejected_low_confidence")
                skipped += 1
                continue

            insert_deal(deal, url, title)
            mark_processed(url, title, "inserted")
            inserted += 1

            print(f"Inserted: {title}")

        except Exception as e:
            print(f"ERROR processing {title}: {e}")
            mark_processed(url, title, "error", str(e))
            errors_count += 1

    print("SUMMARY")
    print(f"Inserted: {inserted}")
    print(f"Skipped: {skipped}")
    print(f"Errors: {errors_count}")


if __name__ == "__main__":
    main()
