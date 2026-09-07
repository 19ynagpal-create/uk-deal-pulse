import os
import json
import time

from google import genai
from google.genai import errors

client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

announcement = """
1 September 2026

Recommended Cash Acquisition of Bodycote plc by Vulcan Alpha Bidco Limited.

The Offer Value is 940 pence per Bodycote share and implies an equity value
of approximately £1.652 billion.

The Offer Value represents a premium of approximately 37.5% to the
three-month volume-weighted average price.

The acquisition is recommended and is intended to be implemented by
means of a scheme of arrangement.

Vulcan Alpha Bidco Limited is indirectly owned by funds managed or
controlled by Veritas Capital.
"""

prompt = f"""
You are extracting structured data for UK Deal Pulse.

Use only facts explicitly supported by the announcement below.
If a field is unsupported, return null.
Do not guess.

Return valid JSON only with these fields:

target_name
acquirer_name
announcement_date
deal_value_gbp
buyer_type
offer_type
offer_price
offer_price_currency
premium_percent
status

Announcement:

{announcement}
"""

response = None

for attempt in range(5):
    try:
        response = client.models.generate_content(
            model="gemini-3.6-flash",
            contents=prompt,
            config={
                "response_mime_type": "application/json"
            },
        )
        break

    except errors.ServerError as e:
        if attempt == 4:
            raise

        wait_seconds = 10 * (attempt + 1)
        print(
            f"Gemini temporarily unavailable. "
            f"Retrying in {wait_seconds} seconds..."
        )
        time.sleep(wait_seconds)

if response is None:
    raise RuntimeError("Gemini did not return a response.")

data = json.loads(response.text)

print("GEMINI EXTRACTION SUCCESS")
print(json.dumps(data, indent=2))
