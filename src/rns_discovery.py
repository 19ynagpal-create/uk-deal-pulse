import os
import requests

TICKER_API_KEY = os.environ["TICKER_API_KEY"]
BASE_URL = "https://api.tickerapp.net/v2/disclosures/sources/rns/items"

headers = {
    "x-api-key": TICKER_API_KEY,
    "accept": "application/json",
}

response = requests.get(
    BASE_URL,
    headers=headers,
    params={"pageSize": 100},
    timeout=30,
)

response.raise_for_status()
payload = response.json()

print("TOP-LEVEL KEYS:", payload.keys())
print("NUMBER OF ITEMS:", len(payload.get("data", [])))

print("\nFIRST 5 ITEMS:")
for item in payload.get("data", [])[:5]:
    print({
        "rnsId": item.get("rnsId"),
        "timestamp": item.get("timestamp"),
        "issuer": item.get("issuer"),
        "headline": item.get("headline"),
    })

print("\nPAGINATION / META:")
for key, value in payload.items():
    if key != "data":
        print(key, "=", value)
