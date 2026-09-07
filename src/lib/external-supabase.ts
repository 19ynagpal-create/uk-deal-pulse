/**
 * External Supabase client (frontend-only).
 *
 * UK Deal Pulse reads its `deals` table from the project owner's own
 * external Supabase project, NOT from Lovable Cloud. Only the public
 * publishable/anon key is used here — no service-role or secret key ever
 * belongs in frontend code. Read access to `verified = true` rows is
 * enforced by Row Level Security on the external project.
 *
 * Configuration (in priority order):
 *   1. Environment variables (browser: VITE_EXTERNAL_SUPABASE_URL /
 *      VITE_EXTERNAL_SUPABASE_PUBLISHABLE_KEY; server/SSR: SUPABASE_URL /
 *      SUPABASE_PUBLISHABLE_KEY)
 *   2. The fallback constants below.
 *
 * The publishable key is a public credential and is safe to keep in the
 * codebase; it grants only the access allowed by the external project's
 * RLS policies (public read of verified deals).
 */

import { createClient } from "@supabase/supabase-js";
import type { Database } from "@/integrations/supabase/types";

// Public, non-secret configuration for the owner's external Supabase project.
const FALLBACK_URL = "https://cczlwhdlsfjhehhkoget.supabase.co";
const FALLBACK_PUBLISHABLE_KEY = "sb_publishable_7p33M4L9f7pSattJfiE9PA_wJZiWLOa";

const EXTERNAL_SUPABASE_URL =
  import.meta.env["VITE_EXTERNAL_SUPABASE_URL"] || FALLBACK_URL;

const EXTERNAL_SUPABASE_PUBLISHABLE_KEY =
  import.meta.env["VITE_EXTERNAL_SUPABASE_PUBLISHABLE_KEY"] ||
  FALLBACK_PUBLISHABLE_KEY;

function isNewSupabaseApiKey(value: string): boolean {
  return value.startsWith("sb_publishable_") || value.startsWith("sb_secret_");
}

function createSupabaseFetch(supabaseKey: string): typeof fetch {
  return (input, init) => {
    const headers = new Headers(
      typeof Request !== "undefined" && input instanceof Request
        ? input.headers
        : undefined,
    );
    if (init?.headers) {
      new Headers(init.headers).forEach((value, key) => headers.set(key, value));
    }
    // New Supabase API keys are opaque strings, not bearer JWTs.
    if (
      isNewSupabaseApiKey(supabaseKey) &&
      headers.get("Authorization") === `Bearer ${supabaseKey}`
    ) {
      headers.delete("Authorization");
    }
    headers.set("apikey", supabaseKey);
    return fetch(input, { ...init, headers });
  };
}

export const externalSupabase = createClient<Database>(
  EXTERNAL_SUPABASE_URL,
  EXTERNAL_SUPABASE_PUBLISHABLE_KEY,
  {
    global: { fetch: createSupabaseFetch(EXTERNAL_SUPABASE_PUBLISHABLE_KEY) },
    auth: {
      persistSession: false,
      autoRefreshToken: false,
      storage: undefined,
    },
  },
);
