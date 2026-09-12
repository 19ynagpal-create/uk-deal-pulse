import os
import time
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

    # Target company publishing the RNS
    if target and target in issuer:
        score += 10

    strong_offer_terms = [
        "recommended cash acquisition",
        "recommended acquisition",
        "firm intention",
        "rule 2.7",
        "recommended offer",
        "scheme of arrangement",
    ]

    weak_offer_terms = [
        "acquisition of",
        "offer for",
    ]

    for term in strong_offer_terms:
        if term in headline:
            score += 8

    for term in weak_offer_terms:
        if term in headline:
            score += 3

    if target and target in headline:
        score += 4

    if acquirer and acquirer in headline:
        score += 3

    # Penalise irrelevant disclosure forms
    bad_terms = [
        "form 8.3",
        "form 8.5",
        "dealing disclosure",
        "holding(s) in company",
        "transaction in own shares",
    ]

    for term in bad_terms:
        if term in headline:
            score -= 15

    return score


def _get_with_retry(params, max_retries=5):
    delay = 3

    for attempt in range(max_retries):
        response = requests.get(
            BASE_URL,
            headers=_headers(),
            params=params,
            timeout=30,
        )

        if response.status_code != 429:
            response.raise_for_status()
            return response

        retry_after = response.headers.get("Retry-After")

        if retry_after:
            wait = int(retry_after)
        else:
            wait = delay

        print(f"Rate limited. Waiting {wait}s before retry...")
        time.sleep(wait)

        delay *= 2

    raise RuntimeError("Ticker API rate limit persisted after retries")


def discover_rns_for_candidate(
    target_name,
    acquirer_name=None,
    lookback_days=90,
    page_size=100,
    max_pages=20,
):
    cutoff = datetime.now(timezone.utc) - timedelta(days=lookback_days)

    cursor = None
    best_match = None
    best_score = 0

    for page_number in range(1, max_pages + 1):
        params = {"pageSize": page_size}

        if cursor:
            params["cursor"] = cursor

        response = _get_with_retry(params)
        payload = response.json()

        items = payload.get("data", [])

        if not items:
            break

        print(f"Scanning RNS page {page_number}: {len(items)} announcements")

        for item in items:
            timestamp = item.get("timestamp")

            if timestamp:
                try:
                    item_date = datetime.fromisoformat(
                        timestamp.replace("Z", "+00:00")
                    )

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

        # Avoid hammering the API
        time.sleep(2)

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
    else:
        print("NO MATCH")
