import os
import time
import requests
from datetime import datetime, timezone


TICKER_API_KEY = os.environ["TICKER_API_KEY"]

BASE_URL = (
    "https://api.tickerapp.net/"
    "v2/disclosures/sources/rns/items"
)

REQUEST_TIMEOUT = 30


def headers():
    return {
        "x-api-key": TICKER_API_KEY,
        "accept": "application/json",
    }


# =========================================================
# API REQUEST WITH RATE-LIMIT RETRY
# =========================================================

def get_page(
    params,
    retries=5,
):
    delay = 3

    for _ in range(retries):

        response = requests.get(
            BASE_URL,
            headers=headers(),
            params=params,
            timeout=REQUEST_TIMEOUT,
        )

        if response.status_code != 429:
            response.raise_for_status()
            return response.json()

        retry_after = response.headers.get(
            "Retry-After"
        )

        if retry_after:
            try:
                wait = int(
                    retry_after
                )
            except ValueError:
                wait = delay
        else:
            wait = delay

        print(
            f"Ticker rate limited — "
            f"waiting {wait}s"
        )

        time.sleep(wait)

        delay *= 2

    raise RuntimeError(
        "Ticker API rate limit persisted "
        "after retries."
    )


# =========================================================
# TAKEOVER HEADLINE FILTER
# =========================================================

def is_likely_takeover(item):

    headline = (
        item.get("headline")
        or ""
    ).lower()

    # Things we do NOT want to treat as deal announcements.
    reject_terms = [
        "form 8.3",
        "form 8.5",
        "opening position disclosure",
        "dealing disclosure",
        "holding(s) in company",
        "transaction in own shares",
        "total voting rights",
        "share buyback",
        "buyback programme",
    ]

    if any(
        term in headline
        for term in reject_terms
    ):
        return False

    takeover_terms = [
        "recommended cash acquisition",
        "recommended acquisition",
        "recommended cash offer",
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


# =========================================================
# TODAY'S RNS FEED
# =========================================================

def get_daily_takeover_rns():

    today = datetime.now(
        timezone.utc
    ).strftime(
        "%Y-%m-%d"
    )

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

        payload = get_page(
            params
        )

        items = payload.get(
            "data",
            [],
        )

        print(
            f"Scanning {today} "
            f"page {page}: "
            f"{len(items)} announcements"
        )

        for item in items:

            if is_likely_takeover(
                item
            ):
                matches.append(
                    item
                )

        paging = (
            payload.get(
                "meta"
            )
            or {}
        ).get(
            "paging"
        ) or {}

        next_cursor = paging.get(
            "nextCursor"
        )

        if not next_cursor:
            break

        cursor = next_cursor

        page += 1

        time.sleep(2)

    return matches


# =========================================================
# GET ONE FULL RNS ITEM
# =========================================================

def get_rns_item(
    rns_identifier,
):

    if not rns_identifier:
        raise ValueError(
            "Missing RNS identifier."
        )

    url = (
        f"{BASE_URL}/"
        f"{rns_identifier}"
    )

    response = requests.get(
        url,
        headers=headers(),
        timeout=REQUEST_TIMEOUT,
    )

    response.raise_for_status()

    payload = response.json()

    item = payload.get(
        "data"
    )

    if not item:
        raise ValueError(
            "Ticker returned no RNS item."
        )

    return item


# =========================================================
# GET HTML PUBLICATION URL
# =========================================================

def get_html_publication_url(
    item,
):

    publications = (
        item.get(
            "publication"
        )
        or []
    )

    for publication in publications:

        if (
            publication.get(
                "mime"
            )
            == "text/html"
        ):
            return publication.get(
                "url"
            )

    return None


# =========================================================
# FETCH FULL ANNOUNCEMENT HTML
# =========================================================

def fetch_rns_html_text(
    item,
):

    html_url = (
        get_html_publication_url(
            item
        )
    )

    if not html_url:
        raise ValueError(
            "RNS item does not contain "
            "an HTML publication URL."
        )

    response = requests.get(
        html_url,
        headers={
            "User-Agent":
                "UKDealPulse/1.0"
        },
        timeout=REQUEST_TIMEOUT,
    )

    response.raise_for_status()

    html = response.text

    if len(html) < 200:
        raise ValueError(
            "RNS HTML publication "
            "returned too little content."
        )

    return (
        html,
        html_url,
    )


# =========================================================
# OPTIONAL LOCAL TEST
# =========================================================

if __name__ == "__main__":

    matches = (
        get_daily_takeover_rns()
    )

    print()

    print(
        "LIKELY TAKEOVER "
        "ANNOUNCEMENTS:",
        len(matches),
    )

    for item in matches:

        print()
        print(
            "RNS ID:",
            item.get(
                "rnsId"
            ),
        )

        print(
            "GUID:",
            item.get(
                "guid"
            ),
        )

        print(
            "ISSUER:",
            (
                item.get(
                    "issuer"
                )
                or {}
            ).get(
                "name"
            ),
        )

        print(
            "HEADLINE:",
            item.get(
                "headline"
            ),
        )
