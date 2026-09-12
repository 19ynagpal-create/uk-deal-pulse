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

    raise RuntimeError(
        "Ticker API rate limit persisted"
    )


def is_likely_takeover(item):
    headline = (
        item.get("headline") or ""
    ).lower()

    reject_terms = [
        "form 8.3",
        "form 8.5",
        "opening position disclosure",
        "dealing disclosure",
        "holding(s) in company",
        "transaction in own shares",
        "total voting rights",
    ]

    if any(
        term in headline
        for term in reject_terms
    ):
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

    return any(
        term in headline
        for term in takeover_terms
    )


def get_daily_takeover_rns():
    today = datetime.now(
        timezone.utc
    ).strftime("%Y-%m-%d")

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

        items = payload.get(
            "data",
            [],
        )

        print(
            f"Scanning {today} page {page}: "
            f"{len(items)} announcements"
        )

        for item in items:
            if is_likely_takeover(item):
                matches.append(item)

        paging = (
            (payload.get("meta") or {})
            .get("paging")
            or {}
        )

        cursor = paging.get(
            "nextCursor"
        )

        if not cursor:
            break

        page += 1
        time.sleep(2)

    return matches


def get_rns_item(rns_identifier):
    url = (
        f"{BASE_URL}/"
        f"{rns_identifier}"
    )

    response = requests.get(
        url,
        headers=headers(),
        timeout=30,
    )

    response.raise_for_status()

    payload = response.json()

    return payload.get("data")


def get_html_publication_url(item):
    publications = (
        item.get("publication")
        or []
    )

    for publication in publications:
        if (
            publication.get("mime")
            == "text/html"
        ):
            return publication.get("url")

    return None


def fetch_rns_html_text(item):
    html_url = get_html_publication_url(
        item
    )

    if not html_url:
        raise ValueError(
            "No HTML publication URL found."
        )

    response = requests.get(
        html_url,
        timeout=30,
        headers={
            "User-Agent":
                "UKDealPulse/1.0"
        },
    )

    response.raise_for_status()

    return (
        response.text,
        html_url,
    )


def expand_rns_item(item):
    guid = item.get("guid")

    if not guid:
        raise ValueError(
            "RNS item has no guid."
        )

    return get_rns_item(guid)


if __name__ == "__main__":
    test_identifier = (
        "urn:newsml:londonstockexchange.com:"
        "20260911:5136U:1"
    )

    print("=" * 70)
    print("TESTING FULL RNS PIPELINE")
    print("=" * 70)

    full_item = get_rns_item(
        test_identifier
    )

    print()
    print("HEADLINE:")
    print(
        full_item.get("headline")
    )

    print()
    print("HTML URL:")
    print(
        get_html_publication_url(
            full_item
        )
    )

    html_text, html_url = (
        fetch_rns_html_text(
            full_item
        )
    )

    print()
    print("HTML FETCH SUCCESS")

    print(
        "Characters:",
        len(html_text),
    )

    print()
    print("Source:")
    print(html_url)
