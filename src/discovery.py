import os
import time
import requests
from datetime import datetime, timezone

TICKER_API_KEY = os.environ["TICKER_API_KEY"]

BASE_URL = "https://api.tickerapp.net/v2/disclosures/sources/rns/items"


def headers():
    return {
        "x-api-key": TICKER_API_KEY,
        "accept": "application/json",
    }


def get_page(params, retries=5):
    delay = 3

    for _ in range(retries):
        response = requests.get(
            BASE_URL,
            headers=headers(),
            params=params,
            timeout=30,
        )

        if response.status_code != 429:
            response.raise_for_status()
            return response.json()

        retry_after = response.headers.get("Retry-After")
        wait = int(retry_after) if retry_after else delay

        print(f"Rate limited — waiting {wait}s")
        time.sleep(wait)
        delay *= 2

    raise RuntimeError("Ticker API rate limit persisted")


def is_likely_takeover(item):
    headline = (item.get("headline") or "").lower()

    reject_terms = [
        "form 8.3",
        "form 8.5",
        "opening position disclosure",
        "dealing disclosure",
        "holding(s) in company",
        "transaction in own shares",
        "total voting rights",
    ]

    if any(term in headline for term in reject_terms):
        return False

    takeover_terms = [
        "recommended cash acquisition",
        "recommended acquisition",
        "recommended offer",
        "firm intention",
        "rule 2.7",
        "scheme of arrangement",
        "acquisition of",
        "offer for",
        "possible offer",
        "cash offer",
        "takeover",
    ]

    return any(term in headline for term in takeover_terms)


def get_daily_takeover_rns():
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    cursor = None
    page = 1
    matches = []

    while True:
        params = {
            "pageSize": 100,
            "dateFrom": today,
            "dateTo": today,
        }

        if cursor:
            params["cursor"] = cursor

        payload = get_page(params)
        items = payload.get("data", [])

        print(
            f"Scanning {today} page {page}: "
            f"{len(items)} announcements"
        )

        for item in items:
            if is_likely_takeover(item):
                matches.append(item)

        paging = (payload.get("meta") or {}).get("paging") or {}
        cursor = paging.get("nextCursor")

        if not cursor:
            break

        page += 1
        time.sleep(2)

    return matches


def get_rns_item(rns_identifier):
    url = f"{BASE_URL}/{rns_identifier}"

    response = requests.get(
        url,
        headers=headers(),
        timeout=30,
    )

    response.raise_for_status()

    payload = response.json()

    return payload.get("data")


if __name__ == "__main__":
    matches = get_daily_takeover_rns()

    print()
    print(
        f"LIKELY TAKEOVER ANNOUNCEMENTS: "
        f"{len(matches)}"
    )

    for index, item in enumerate(matches, start=1):
        print()
        print("=" * 70)
        print(f"MATCH {index}")
        print("=" * 70)

        print("RAW LIST ITEM:")
        print(item)

        print()
        print("AVAILABLE KEYS:")
        print(list(item.keys()))

        possible_ids = [
            item.get("id"),
            item.get("guid"),
            item.get("identifier"),
            item.get("rnsDateId"),
            item.get("rnsId"),
        ]

        possible_ids = [
            x for x in possible_ids
            if x
        ]

        print()
        print("POSSIBLE IDENTIFIERS:")
        for value in possible_ids:
            print(value)

        full_identifier = None

        for value in possible_ids:
            if (
                isinstance(value, str)
                and value.startswith("urn:newsml:")
            ):
                full_identifier = value
                break

        if not full_identifier:
            print()
            print(
                "No full urn:newsml identifier found "
                "in this item."
            )
            continue

        print()
        print("FULL IDENTIFIER:")
        print(full_identifier)

        try:
            full_item = get_rns_item(
                full_identifier
            )

            print()
            print("FULL RNS ITEM:")
            print(full_item)

        except Exception as exc:
            print()
            print(
                f"FULL ITEM FETCH ERROR: {exc}"
            )
