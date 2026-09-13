# UK Deal Pulse

UK Deal Pulse is an automated UK public M&A intelligence platform that tracks takeover activity, structures primary-source announcements and presents deal analytics in a searchable interface.

## Live site

[UK Deal Pulse](https://uk-deal-pulse.lovable.app))

## What it does

- Tracks selected UK public takeover activity
- Monitors current Takeover Panel offer situations
- Checks RNS announcements automatically
- Extracts structured transaction data from source documents
- Applies validation and duplicate checks before publication
- Provides searchable deal data, analytics and adviser rankings

## Data captured

The platform structures fields including:

- Target
- Acquirer
- Announcement date
- Deal value
- Sector
- Buyer type
- Offer structure
- Offer price
- Premium
- Advisers
- Financing
- Status
- Strategic rationale
- Source information

## Automation

The automated pipeline runs daily:

Takeover Panel  
→ RNS discovery  
→ candidate matching  
→ full announcement retrieval  
→ structured extraction  
→ validation  
→ duplicate checking  
→ Supabase  
→ live website

## Tech stack

- Python
- Supabase
- SQL
- Gemini API
- Ticker RNS API
- GitHub Actions
- Lovable
- React / TypeScript

## Methodology

UK Deal Pulse uses public primary-source information, including Takeover Panel disclosures and RNS announcements.

AI is used to assist structured extraction from source documents. Unsupported information is left undisclosed rather than estimated.

The dataset may be incomplete and should not be relied upon as investment advice.

## Author

Built and maintained by Yash Nagpal.
