CREATE TABLE public.deals (
  id UUID NOT NULL DEFAULT gen_random_uuid() PRIMARY KEY,
  target_name TEXT NOT NULL,
  acquirer_name TEXT NOT NULL,
  announcement_date DATE NOT NULL,
  deal_value_gbp NUMERIC,
  sector TEXT,
  buyer_type TEXT,
  acquirer_country TEXT,
  offer_type TEXT,
  offer_price NUMERIC,
  offer_price_currency TEXT,
  premium_percent NUMERIC,
  buyer_advisers TEXT[] NOT NULL DEFAULT '{}',
  target_advisers TEXT[] NOT NULL DEFAULT '{}',
  status TEXT NOT NULL DEFAULT 'Announced',
  financing TEXT,
  strategic_rationale TEXT,
  source_url TEXT NOT NULL,
  source_title TEXT,
  source_domain TEXT,
  ai_confidence NUMERIC,
  verified BOOLEAN NOT NULL DEFAULT false,
  auto_publish_eligible BOOLEAN NOT NULL DEFAULT false,
  created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
  updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now()
);

CREATE TABLE public.processed_sources (
  id UUID NOT NULL DEFAULT gen_random_uuid() PRIMARY KEY,
  source_url TEXT NOT NULL UNIQUE,
  source_title TEXT,
  discovered_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
  processed_at TIMESTAMP WITH TIME ZONE,
  processing_status TEXT NOT NULL DEFAULT 'pending',
  error_message TEXT
);

CREATE INDEX deals_announcement_date_idx ON public.deals (announcement_date DESC);
CREATE INDEX deals_sector_idx ON public.deals (sector);
CREATE INDEX deals_buyer_type_idx ON public.deals (buyer_type);
CREATE INDEX deals_verified_idx ON public.deals (verified);
CREATE INDEX processed_sources_status_idx ON public.processed_sources (processing_status);

GRANT SELECT ON public.deals TO anon;
GRANT SELECT ON public.deals TO authenticated;
GRANT ALL ON public.deals TO service_role;
GRANT ALL ON public.processed_sources TO service_role;

ALTER TABLE public.deals ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.processed_sources ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Verified deals are publicly readable"
  ON public.deals FOR SELECT TO anon, authenticated
  USING (verified = true);

CREATE OR REPLACE FUNCTION public.set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = now();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql SET search_path = public;

CREATE TRIGGER deals_set_updated_at
  BEFORE UPDATE ON public.deals
  FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();