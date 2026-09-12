import os
import requests
from datetime import datetime, timedelta, timezone

TICKER_API_KEY = os.environ["TICKER_API_KEY"]
BASE_URL = "https://api.tickerapp.net/v2/disclosures/sources/rns/items"


def _headers():
    return {
        "x-api-key": TICKER_API_KEY,
        "accept": "application/json",
    }


def _normalise(value):
    return (value or "").lower().strip()


def _score_item(item, target_name, acquirer_name=None):
    issuer = _normalise((item.get("issuer") or {}).get("name"))
    headline = _normalise(item.get("headline"))

    target = _normalise(target_name)
    acquirer = _normalise(acquirer_name)

    score = 0

    # Target company publishing the RNS is a very strong signal
    if target and target in issuer:
        score += 10

    offer_terms = [
        "recommended cash acquisition",
        "recommended acquisition",
        "firm intention",
        "rule 2.7",
        "recommended offer",
        "scheme of arrangement",
        "acquisition of",
        "offer for",
    ]

    for term in offer_terms:
        if term in headline:
            score += 5

    if target and target in headline:
        score += 4

    if acquirer and acquirer in headline:
        score += 3

    return score


def discover_rns_for_candidate(
    target_name,
    acquirer_name=None,
    lookback_days=90,
    page_size=100,
    max_pages=20,
):
    """
    Search backwards through RNS announcements for the most likely
    takeover announcement relating to a Takeover Panel candidate.
    """

    cutoff = datetime.now(timezone.utc) - timedelta(days=lookback_days)

    cursor = None
    best_match = None
    best_score = 0

    for page_number in range(1, max_pages + 1):

        params = {
            "pageSize": page_size,
        }

        if cursor:
            params["cursor"] = cursor

        response = requests.get(
            BASE_URL,
            headers=_headers(),
            params=params,
            timeout=30,
        )

        response.raise_for_status()

        payload = response.json()
        items = payload.get("data", [])

        if not items:
            break

        print(
            f"Scanning RNS page {page_number}: "
            f"{len(items)} announcements"
        )

        oldest_timestamp = None

        for item in items:
            timestamp = item.get("timestamp")

            if timestamp:
                try:
                    item_date = datetime.fromisoformat(
                        timestamp.replace("Z", "+00:00")
                    )

                    oldest_timestamp = item_date

                    if item_date < cutoff:
                        print("Reached lookback limit")
                        return best_match

                except ValueError:
                    pass

            score = _score_item(
                item,
                target_name=target_name,
                acquirer_name=acquirer_name,
            )

            if score > best_score:
                best_score = score
                best_match = item

                print(
                    "Possible match:",
                    score,
                    (item.get("issuer") or {}).get("name"),
                    "-",
                    item.get("headline"),
                )

        paging = (payload.get("meta") or {}).get("paging") or {}
        next_cursor = paging.get("nextCursor")

        if not next_cursor:
            break

        cursor = next_cursor

    # Require a reasonably strong match
    if best_score < 10:
        return None

    return best_match


if __name__ == "__main__":

    result = discover_rns_for_candidate(
        target_name="SEGRO plc",
        acquirer_name="Prologis",
        lookback_days=90,
    )

    print()

    if result:
        print("FOUND RNS")
        print("RNS ID:", result.get("rnsId"))
        print("DATE:", result.get("timestamp"))
        print("ISSUER:", (result.get("issuer") or {}).get("name"))
        print("HEADLINE:", result.get("headline"))
        print(result)
    else:
        print("NO MATCH")
