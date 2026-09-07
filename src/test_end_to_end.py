import os
import json
import time
import requests

from google import genai
from google.genai import errors

GEMINI_API_KEY = os.environ["GEMINI_API_KEY"]
SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_KEY = os.environ["SUPABASE_SERVICE_ROLE_KEY"]

SOURCE_URL = "https://www.investegate.co.uk/announcement/rns/ramsdens-holdings--rfx/final-recommended-cash-offer/9671448"

SOURCE_TEXT = """
16 July 2026

FINAL RECOMMENDED CASH OFFER FOR RAMSDENS HOLDINGS PLC
BY CHESS BIDCO LIMITED
(an indirect wholly-owned subsidiary of FirstCash Holdings, Inc.)

The boards of Chess Bidco Limited and Ramsdens Holdings PLC announced
that they had reached agreement on the terms of a recommended cash acquisition
pursuant to which Bidco would acquire the entire issued and to be issued
share capital of Ramsdens.

The acquisition is to be effected by means of a Court-sanctioned Scheme
of Arrangement under Part 26 of the Companies Act 2006.

The parties announced a revised offer increasing the cash price to be
received by Ramsdens shareholders.
"""

client = genai.Client(api_key=GEMINI_API_KEY)


def headers():
    return {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
    }


def extract_deal():
    prompt = f"""
You are the structured-data extraction engine for UK Deal Pulse.

Use only the supplied source text.

If a field is unsupported, return null.
Never guess.
Never calculate a premium unless explicitly stated.

Return valid JSON only with these fields:

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
{SOURCE_TEXT}
"""

    for attempt in range(5):
        try:
            response = client.models.generate_content(
                model="gemini-3.6-flash",
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

    raise RuntimeError("Gemini extraction failed")


def duplicate_exists(deal):
    params = {
        "select": "id,target_name,acquirer_name,announcement_date",
        "or": (
            f"(source_url.eq.{SOURCE_URL},"
            f"and(target_name.eq.{deal['target_name']},"
            f"acquirer_name.eq.{deal['acquirer_name']},"
            f"announcement_date.eq.{deal['announcement_date']}))"
        ),
        "limit": "1",
    }

    r = requests.get(
        f"{SUPABASE_URL}/rest/v1/deals",
        headers=headers(),
        params=params,
        timeout=30,
    )
    r.raise_for_status()
    return bool(r.json())


def validate(deal):
    required = [
        "target_name",
        "acquirer_name",
        "announcement_date",
    ]

    for field in required:
        if not deal.get(field):
            raise ValueError(f"Missing required field: {field}")

    confidence = deal.get("confidence")
    if confidence is None:
        raise ValueError("Missing confidence")

    return float(confidence)


def insert_deal(deal):
    confidence = validate(deal)

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
        "source_url": SOURCE_URL,
        "source_title": "Final Recommended Cash Offer",
        "source_domain": "investegate.co.uk",
        "ai_confidence": confidence,
        "verified": confidence >= 0.92,
        "auto_publish_eligible": confidence >= 0.92,
    }

    r = requests.post(
        f"{SUPABASE_URL}/rest/v1/deals",
        headers={**headers(), "Prefer": "return=representation"},
        json=payload,
        timeout=30,
    )
    r.raise_for_status()

    return r.json()


def main():
    print("Extracting deal with Gemini...")
    deal = extract_deal()

    print("EXTRACTED:")
    print(json.dumps(deal, indent=2))

    validate(deal)

    if duplicate_exists(deal):
        print("DUPLICATE: deal already exists")
        return

    result = insert_deal(deal)

    print("INSERT SUCCESS")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
