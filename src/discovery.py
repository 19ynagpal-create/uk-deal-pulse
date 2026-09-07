import requests
from bs4 import BeautifulSoup

DISCLOSURE_URL = "https://www.thetakeoverpanel.org.uk/disclosure/disclosure-table"


def discover_candidates():
    r = requests.get(
        DISCLOSURE_URL,
        headers={
            "User-Agent": "UKDealPulse/1.0"
        },
        timeout=30,
    )
    r.raise_for_status()

    soup = BeautifulSoup(r.text, "html.parser")

    text = soup.get_text("\n", strip=True)

    candidates = []

    blocks = text.split("OFFEREE:")

    for block in blocks[1:]:
        lines = [
            line.strip()
            for line in block.splitlines()
            if line.strip()
        ]

        if not lines:
            continue

        offeree = lines[0]

        offeror = None

        for line in lines:
            if line.startswith("OFFEROR:"):
                offeror = line.replace("OFFEROR:", "").strip()
                break

        if not offeror:
            continue

        candidates.append(
            {
                "target_name": offeree,
                "acquirer_name": offeror,
            }
        )

    return candidates


if __name__ == "__main__":
    rows = discover_candidates()

    print(f"Discovered {len(rows)} offer-period candidates")

    for row in rows[:20]:
        print(row)
