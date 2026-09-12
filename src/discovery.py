
import re
import requests
from bs4 import BeautifulSoup


DISCLOSURE_TABLE_URL = (
    "https://www.thetakeoverpanel.org.uk/"
    "disclosure/disclosure-table"
)

REQUEST_TIMEOUT = 30

HTTP_HEADERS = {
    "User-Agent": "UKDealPulse/1.0"
}


def clean_name(value):
    value = (value or "").strip()

    # Remove anything after the LEI separator
    value = re.split(
        r"\s+\|\s+LEI:",
        value,
        maxsplit=1,
        flags=re.IGNORECASE,
    )[0]

    return value.strip()


def discover_candidates():
    """
    Read the Takeover Panel Disclosure Table and return
    named target / acquirer combinations.

    Returns:
    [
        {
            "target_name": "...",
            "acquirer_name": "..."
        },
        ...
    ]
    """

    response = requests.get(
        DISCLOSURE_TABLE_URL,
        headers=HTTP_HEADERS,
        timeout=REQUEST_TIMEOUT,
    )

    response.raise_for_status()

    soup = BeautifulSoup(
        response.text,
        "html.parser",
    )

    text = soup.get_text(
        "\n",
        strip=True,
    )

    lines = [
        line.strip()
        for line in text.splitlines()
        if line.strip()
    ]

    candidates = []
    seen = set()

    current_target = None

    for line in lines:

        # ---------------------------------------------
        # OFFEREE / TARGET
        # ---------------------------------------------

        if line.upper().startswith("OFFEREE:"):

            current_target = clean_name(
                line.split(
                    ":",
                    1,
                )[1]
            )

            continue

        # ---------------------------------------------
        # OFFEROR / ACQUIRER
        # ---------------------------------------------

        if line.upper().startswith("OFFEROR:"):

            if not current_target:
                continue

            acquirer = clean_name(
                line.split(
                    ":",
                    1,
                )[1]
            )

            if not acquirer:
                continue

            if (
                acquirer.lower()
                == "no named offeror"
            ):
                continue

            key = (
                current_target.lower(),
                acquirer.lower(),
            )

            if key in seen:
                continue

            seen.add(key)

            candidates.append({
                "target_name":
                    current_target,

                "acquirer_name":
                    acquirer,
            })

    return candidates


if __name__ == "__main__":

    results = discover_candidates()

    print(
        f"Candidates found: "
        f"{len(results)}"
    )

    print()

    for candidate in results:
        print(
            candidate["target_name"],
            "<-",
            candidate["acquirer_name"],
        )
