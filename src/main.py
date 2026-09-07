import re
from datetime import datetime, timezone

import requests

from discovery import discover_candidates


SUPABASE_URL = __import__("os").environ["SUPABASE_URL"]
SUPABASE_KEY = __import__("os").environ["SUPABASE_SERVICE_ROLE_KEY"]


def headers():
    return {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
    }


def slugify(value):
    value = value.lower()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    return value.strip("-")


def candidate_key(target, acquirer):
    return (
        "takeover-panel://"
        + slugify(target)
        + "/"
        + slugify(acquirer)
    )


def already_seen(key):
    r = requests.get(
        f"{SUPABASE_URL}/rest/v1/processed_sources",
        headers=headers(),
        params={
            "select": "id",
            "source_url": f"eq.{key}",
            "limit": "1",
        },
        timeout=30,
    )

    r.raise_for_status()
    return bool(r.json())


def save_candidate(target, acquirer):
    key = candidate_key(target, acquirer)

    payload = {
        "source_url": key,
        "source_title": f"{target} ← {acquirer}",
        "discovered_at": datetime.now(timezone.utc).isoformat(),
        "processed_at": None,
        "processing_status": "discovered_candidate",
        "error_message": None,
    }

    r = requests.post(
        f"{SUPABASE_URL}/rest/v1/processed_sources",
        headers={
            **headers(),
            "Prefer": "return=minimal",
        },
        json=payload,
        timeout=30,
    )

    r.raise_for_status()


def main():
    print("UK Deal Pulse weekly discovery")
    print("=" * 60)

    candidates = discover_candidates()

    print(f"Current Takeover Panel candidates: {len(candidates)}")

    new_candidates = 0
    already_known = 0

    for candidate in candidates:
        target = candidate.get("target_name")
        acquirer = candidate.get("acquirer_name")

        if not target or not acquirer:
            continue

        key = candidate_key(target, acquirer)

        if already_seen(key):
            already_known += 1
            continue

        save_candidate(target, acquirer)
        new_candidates += 1

        print()
        print("NEW OFFER SITUATION")
        print(f"Target: {target}")
        print(f"Offeror: {acquirer}")

    print()
    print("=" * 60)
    print("UK DEAL PULSE WEEKLY SUMMARY")
    print("=" * 60)
    print(f"Current candidates: {len(candidates)}")
    print(f"New candidates: {new_candidates}")
    print(f"Already known: {already_known}")
    print("Errors: 0")


if __name__ == "__main__":
    main()
