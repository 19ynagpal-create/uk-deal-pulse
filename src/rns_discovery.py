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

    # Strongest signal: target company itself published the RNS
    if target and target in issuer:
        score += 10

    # Useful offer-related headlines
    offer_terms = [
        "recommended cash acquisition",
        "recommended acquisition",
        "firm intention",
        "rule 2.7",
        "offer for",
        "scheme of arrangement",
        "recommended offer",
        "acquisition of",
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
    lookback_days=60,
    page_size=100,
):
    """
    Finds the most likely takeover RNS for a Takeover Panel candidate.

    Returns:
        dict | None
    """

    cutoff = datetime.now(timezone.utc) - timedelta(days=lookback_days)

    response = requests.get(
        BASE_URL,
        headers=_headers(),
        params={"pageSize": page_size},
        timeout=30,
    )
    response.raise_for_status()

    payload = response.json()
    items = payload.get("data", [])

    candidates = []

    for item in items:
        timestamp = item.get("timestamp")

        if timestamp:
            try:
                item_date = datetime.fromisoformat(
                    timestamp.replace("Z", "+00:00")
                )
                if item_date < cutoff:
                    continue
            except ValueError:
                pass

        score = _score_item(
            item,
            target_name=target_name,
            acquirer_name=acquirer_name,
        )

        if score > 0:
            candidates.append((score, item))

    if not candidates:
        return None

    candidates.sort(
        key=lambda x: (
            x[0],
            x[1].get("timestamp", ""),
        ),
        reverse=True,
    )

    best_score, best_item = candidates[0]

    # Do not trust weak matches
    if best_score < 10:
        return None

    return best_item


if __name__ == "__main__":
    # Temporary test
    result = discover_rns_for_candidate(
        target_name="SEGRO plc",
        acquirer_name="Prologis, Inc.",
    )

    if result:
        print("FOUND RNS")
        print(result)
    else:
        print("NO MATCH")
