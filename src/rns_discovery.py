import os
import time
import requests
from datetime import datetime, timedelta

TICKER_API_KEY = os.environ["TICKER_API_KEY"]

BASE_URL = "https://api.tickerapp.net/v2/disclosures/sources/rns/items"


def headers():
    return {
        "x-api-key": TICKER_API_KEY,
        "accept": "application/json",
    }


def normalise(value):
    return (value or "").lower().strip()


def score_item(item, target_name, acquirer_name=None):
    issuer = normalise((item.get("issuer") or {}).get("name"))
    headline = normalise(item.get("headline"))

    target = normalise(target_name)
    acquirer = normalise(acquirer_name)

    score = 0

    # Strongest signal
    if target and target in issuer:
        score += 12

    if target and target in headline:
        score += 5

    if acquirer and acquirer in headline:
        score += 4

    takeover_terms = [
        "recommended cash acquisition",
        "recommended acquisition",
        "recommended offer",
        "firm intention",
        "rule 2.7",
        "scheme of arrangement",
        "acquisition of",
        "offer for",
    ]

    for term in takeover_terms:
        if term in headline:
            score += 6

    # Reject common irrelevant takeover disclosures
    bad_terms = [
        "form 8.3",
        "form 8.5",
        "dealing disclosure",
        "holding(s) in company",
        "transaction in own shares",
        "opening position disclosure",
    ]

    for term in bad_terms:
        if term in headline:
            score -= 20

    return score


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


def search_day(target_name, acquirer_name, search_date):
    date_string = search_date.strftime("%Y-%m-%d")

    cursor = None
    best_item = None
    best_score = 0
    page = 1

    while True:
        params = {
            "pageSize": 100,
            "dateFrom": date_string,
            "dateTo": date_string,
        }

        if cursor:
            params["cursor"] = cursor

        payload = get_page(params)

        items = payload.get("data", [])

        print(
            f"{date_string} — page {page}: "
            f"{len(items)} announcements"
        )

        for item in items:
            score = score_item(
                item,
                target_name,
                acquirer_name,
            )

            if score > best_score:
                best_score = score
                best_item = item

                print(
                    "Possible match:",
                    score,
                    (item.get("issuer") or {}).get("name"),
                    "-",
                    item.get("headline"),
                )

        paging = (payload.get("meta") or {}).get("paging") or {}
        cursor = paging.get("nextCursor")

        if not cursor:
            break

        page += 1
        time.sleep(1)

    if best_score >= 12:
        return best_item

    return None


def discover_rns_for_candidate(
    target_name,
    acquirer_name,
    approximate_date,
    days_before=3,
    days_after=3,
):
    """
    Search a narrow date window around the expected announcement date.
    Free-tier compatible: only uses dateFrom/dateTo.
    """

    if isinstance(approximate_date, str):
        approximate_date = datetime.strptime(
            approximate_date,
            "%Y-%m-%d"
        )

    for offset in range(0, max(days_before, days_after) + 1):

        dates = []

        if offset == 0:
            dates.append(approximate_date)

        else:
            if offset <= days_before:
                dates.append(
                    approximate_date - timedelta(days=offset)
                )

            if offset <= days_after:
                dates.append(
                    approximate_date + timedelta(days=offset)
                )

        for date in dates:

            print()
            print("Searching:", date.strftime("%Y-%m-%d"))

            result = search_day(
                target_name,
                acquirer_name,
                date,
            )

            if result:
                return result

    return None


if __name__ == "__main__":

    # Known test case
    result = discover_rns_for_candidate(
        target_name="SEGRO plc",
        acquirer_name="Prologis",
        approximate_date="2026-08-04",
        days_before=1,
        days_after=1,
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
