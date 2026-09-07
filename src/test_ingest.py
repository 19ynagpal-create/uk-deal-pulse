import os
import requests

SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_KEY = os.environ["SUPABASE_SERVICE_ROLE_KEY"]

TEST_DEAL = {
    "target_name": "Bodycote plc",
    "acquirer_name": "Vulcan Alpha Bidco Limited",
    "announcement_date": "2026-09-01",
    "deal_value_gbp": 1652000000,
    "sector": "Industrials",
    "buyer_type": "Private Equity",
    "offer_type": "Cash",
    "offer_price": 940,
    "offer_price_currency": "GBp",
    "premium_percent": 37.5,
    "status": "Recommended",
    "source_url": "https://www.investegate.co.uk/announcement/rns/bodycote--boy/recommended-cash-acquisition-of-bodycote-plc/9747189",
    "source_title": "Recommended Cash Acquisition of Bodycote plc",
    "verified": True
}

def supabase_headers():
    return {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
    }

def find_duplicate():
    params = {
        "select": "id,target_name,acquirer_name,announcement_date,source_url",
        "source_url": f"eq.{TEST_DEAL['source_url']}",
        "limit": "1",
    }

    r = requests.get(
        f"{SUPABASE_URL}/rest/v1/deals",
        headers=supabase_headers(),
        params=params,
        timeout=30,
    )
    r.raise_for_status()
    return r.json()

def main():
    duplicate = find_duplicate()

    if duplicate:
        print("SUCCESS: duplicate detected")
        print("No new row inserted")
        return

    r = requests.post(
        f"{SUPABASE_URL}/rest/v1/deals",
        headers={
            **supabase_headers(),
            "Prefer": "return=representation",
        },
        json=TEST_DEAL,
        timeout=30,
    )
    r.raise_for_status()

    print("WARNING: no duplicate was found, so a row was inserted")
    print(r.json())

if __name__ == "__main__":
    main()
