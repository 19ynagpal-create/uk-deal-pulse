/**
 * Deal data layer.
 *
 * All records come from the `deals` table in the project database and only
 * rows with `verified = true` are ever exposed (enforced both here and by the
 * database access policy). If no verified records exist, every accessor
 * returns an empty result so the UI can show an honest empty state instead of
 * fabricated statistics.
 */

import { supabase } from "@/integrations/supabase/client";

export type BuyerType = "Strategic" | "Private Equity";
export type DealStatus =
  | "Announced"
  | "Recommended"
  | "Completed"
  | "Withdrawn"
  | "Other";

export interface Deal {
  id: string;
  target: string;
  acquirer: string;
  acquirerCountry: string;
  sector: string;
  announcementDate: string; // ISO date
  dealValueGbpM: number | null;
  offerPrice: number | null;
  offerPriceCurrency: string | null;
  premiumPct: number | null;
  buyerType: BuyerType;
  status: DealStatus;
  offerType: string | null;
  rationale: string | null;
  financing: string | null;
  targetAdvisers: string[];
  buyerAdvisers: string[];
  sources: { label: string; url: string }[];
}

/** Data is live from the database, never sample records. */
export const IS_SAMPLE_DATA = false;

const UNKNOWN_SECTOR = "Unclassified";

const STATUSES: DealStatus[] = [
  "Announced",
  "Recommended",
  "Completed",
  "Withdrawn",
  "Other",
];

type DealRow = {
  id: string;
  target_name: string;
  acquirer_name: string;
  announcement_date: string;
  deal_value_gbp: number | string | null;
  sector: string | null;
  buyer_type: string | null;
  acquirer_country: string | null;
  offer_type: string | null;
  offer_price: number | string | null;
  offer_price_currency: string | null;
  premium_percent: number | string | null;
  buyer_advisers: string[] | null;
  target_advisers: string[] | null;
  status: string | null;
  financing: string | null;
  strategic_rationale: string | null;
  source_url: string | null;
  source_title: string | null;
  source_domain: string | null;
};

const num = (v: number | string | null): number | null => {
  if (v == null) return null;
  const n = typeof v === "number" ? v : Number(v);
  return Number.isFinite(n) ? n : null;
};

function mapRow(row: DealRow): Deal {
  const valueGbp = num(row.deal_value_gbp);
  const status = STATUSES.includes(row.status as DealStatus)
    ? (row.status as DealStatus)
    : "Other";
  const sourceUrl = row.source_url ?? "";
  return {
    id: row.id,
    target: row.target_name,
    acquirer: row.acquirer_name,
    acquirerCountry: row.acquirer_country ?? "Not disclosed",
    sector: row.sector ?? UNKNOWN_SECTOR,
    announcementDate: row.announcement_date,
    dealValueGbpM: valueGbp == null ? null : valueGbp / 1_000_000,
    offerPrice: num(row.offer_price),
    offerPriceCurrency: row.offer_price_currency,
    premiumPct: num(row.premium_percent),
    buyerType: row.buyer_type === "Private Equity" ? "Private Equity" : "Strategic",
    status,
    offerType: row.offer_type,
    rationale: row.strategic_rationale,
    financing: row.financing,
    targetAdvisers: (row.target_advisers ?? []).filter(Boolean),
    buyerAdvisers: (row.buyer_advisers ?? []).filter(Boolean),
    sources: sourceUrl
      ? [{ label: row.source_title ?? row.source_domain ?? "Source", url: sourceUrl }]
      : [],
  };
}

const SELECT_COLUMNS =
  "id,target_name,acquirer_name,announcement_date,deal_value_gbp,sector,buyer_type,acquirer_country,offer_type,offer_price,offer_price_currency,premium_percent,buyer_advisers,target_advisers,status,financing,strategic_rationale,source_url,source_title,source_domain";

const byDateDesc = (a: Deal, b: Deal) =>
  b.announcementDate.localeCompare(a.announcementDate);

/** Verified records only. */
async function source(): Promise<Deal[]> {
  const { data, error } = await supabase
    .from("deals")
    .select(SELECT_COLUMNS)
    .eq("verified", true)
    .order("announcement_date", { ascending: false })
    .limit(2000);
  if (error) throw new Error(error.message);
  return ((data ?? []) as unknown as DealRow[]).map(mapRow).sort(byDateDesc);
}

export interface DealQuery {
  search?: string | undefined;
  sector?: string | undefined;
  buyerType?: string | undefined;
  status?: string | undefined;
  adviser?: string | undefined;
  minValue?: number | undefined;
  fromDate?: string | undefined;
  sort?:
    | "newest"
    | "oldest"
    | "largest"
    | "smallest"
    | "premium-high"
    | "premium-low"
    | undefined;
  page?: number | undefined;
  pageSize?: number | undefined;
}

export interface DealPage {
  rows: Deal[];
  total: number;
  page: number;
  pageSize: number;
}

function matches(deal: Deal, q: DealQuery) {
  const search = q.search?.trim().toLowerCase();
  if (
    search &&
    ![deal.target, deal.acquirer, deal.sector].some((f) =>
      f.toLowerCase().includes(search),
    )
  )
    return false;
  if (q.sector && q.sector !== "all" && deal.sector !== q.sector) return false;
  if (q.buyerType && q.buyerType !== "all" && deal.buyerType !== q.buyerType)
    return false;
  if (q.status && q.status !== "all" && deal.status !== q.status) return false;
  if (
    q.adviser &&
    q.adviser !== "all" &&
    ![...deal.targetAdvisers, ...deal.buyerAdvisers].includes(q.adviser)
  )
    return false;
  if (q.minValue && (deal.dealValueGbpM ?? 0) < q.minValue) return false;
  if (q.fromDate && deal.announcementDate < q.fromDate) return false;
  return true;
}

function sortDeals(rows: Deal[], sort: DealQuery["sort"]) {
  const v = (d: Deal) => d.dealValueGbpM ?? -1;
  const p = (d: Deal) => d.premiumPct ?? -1;
  switch (sort) {
    case "oldest":
      return rows.sort((a, b) => a.announcementDate.localeCompare(b.announcementDate));
    case "largest":
      return rows.sort((a, b) => v(b) - v(a));
    case "smallest":
      return rows.sort((a, b) => v(a) - v(b));
    case "premium-high":
      return rows.sort((a, b) => p(b) - p(a));
    case "premium-low":
      return rows.sort((a, b) => p(a) - p(b));
    default:
      return rows.sort(byDateDesc);
  }
}

export function median(values: number[]): number | null {
  const nums = values.filter((n) => Number.isFinite(n)).sort((a, b) => a - b);
  if (!nums.length) return null;
  const mid = Math.floor(nums.length / 2);
  if (nums.length % 2) return nums[mid] ?? null;
  const a = nums[mid - 1] ?? 0;
  const b = nums[mid] ?? 0;
  return (a + b) / 2;
}

export interface HeadlineStats {
  dealCount: number;
  totalValueGbpM: number;
  medianPremiumPct: number | null;
  dealsThisWeek: number;
}

export interface WeeklySummary {
  newDeals: number;
  totalValueGbpM: number;
  largest: Deal | null;
  medianPremiumPct: number | null;
  mostActiveSector: string | null;
  deals: Deal[];
  windowStart: string;
}

export interface AdviserRow {
  adviser: string;
  deals: number;
  totalValueGbpM: number;
  averageValueGbpM: number;
}

function daysAgoISO(days: number) {
  const d = new Date();
  d.setUTCDate(d.getUTCDate() - days);
  return d.toISOString().slice(0, 10);
}

export const dealsRepository = {
  async list(query: DealQuery = {}): Promise<DealPage> {
    const all = await source();
    const filtered = sortDeals(all.filter((d) => matches(d, query)), query.sort);
    const page = query.page ?? 1;
    const pageSize = query.pageSize ?? 10;
    return {
      rows: filtered.slice((page - 1) * pageSize, page * pageSize),
      total: filtered.length,
      page,
      pageSize,
    };
  },

  async getById(id: string): Promise<Deal | null> {
    const { data, error } = await supabase
      .from("deals")
      .select(SELECT_COLUMNS)
      .eq("verified", true)
      .eq("id", id)
      .maybeSingle();
    if (error) throw new Error(error.message);
    return data ? mapRow(data as unknown as DealRow) : null;
  },

  async headlineStats(): Promise<HeadlineStats> {
    const all = await source();
    const weekStart = daysAgoISO(7);
    return {
      dealCount: all.length,
      totalValueGbpM: all.reduce((s, d) => s + (d.dealValueGbpM ?? 0), 0),
      medianPremiumPct: median(
        all.map((d) => d.premiumPct).filter((n): n is number => n != null),
      ),
      dealsThisWeek: all.filter((d) => d.announcementDate >= weekStart).length,
    };
  },

  async weeklySummary(): Promise<WeeklySummary> {
    const all = await source();
    const windowStart = daysAgoISO(7);
    const deals = all.filter((d) => d.announcementDate >= windowStart);
    const sectors = new Map<string, number>();
    deals.forEach((d) => sectors.set(d.sector, (sectors.get(d.sector) ?? 0) + 1));
    const mostActiveSector =
      [...sectors.entries()].sort((a, b) => b[1] - a[1])[0]?.[0] ?? null;
    return {
      newDeals: deals.length,
      totalValueGbpM: deals.reduce((s, d) => s + (d.dealValueGbpM ?? 0), 0),
      largest:
        [...deals].sort((a, b) => (b.dealValueGbpM ?? 0) - (a.dealValueGbpM ?? 0))[0] ??
        null,
      medianPremiumPct: median(
        deals.map((d) => d.premiumPct).filter((n): n is number => n != null),
      ),
      mostActiveSector,
      deals,
      windowStart,
    };
  },

  async byMonth() {
    const all = await source();
    const map = new Map<string, { month: string; deals: number; value: number }>();
    all.forEach((d) => {
      const month = d.announcementDate.slice(0, 7);
      const row = map.get(month) ?? { month, deals: 0, value: 0 };
      row.deals += 1;
      row.value += d.dealValueGbpM ?? 0;
      map.set(month, row);
    });
    return [...map.values()].sort((a, b) => a.month.localeCompare(b.month));
  },

  async bySector() {
    const all = await source();
    const map = new Map<
      string,
      { sector: string; deals: number; value: number; premiums: number[] }
    >();
    all.forEach((d) => {
      const row =
        map.get(d.sector) ?? { sector: d.sector, deals: 0, value: 0, premiums: [] };
      row.deals += 1;
      row.value += d.dealValueGbpM ?? 0;
      if (d.premiumPct != null) row.premiums.push(d.premiumPct);
      map.set(d.sector, row);
    });
    return [...map.values()]
      .map((r) => ({
        sector: r.sector,
        deals: r.deals,
        value: r.value,
        medianPremiumPct: median(r.premiums),
      }))
      .sort((a, b) => b.value - a.value);
  },

  async byBuyerType() {
    const all = await source();
    const types: BuyerType[] = ["Strategic", "Private Equity"];
    return types.map((type) => {
      const rows = all.filter((d) => d.buyerType === type);
      return {
        type,
        deals: rows.length,
        value: rows.reduce((s, d) => s + (d.dealValueGbpM ?? 0), 0),
      };
    });
  },

  async byBuyerOrigin() {
    const all = await source();
    const uk = all.filter((d) => d.acquirerCountry === "United Kingdom");
    return [
      {
        origin: "UK buyers",
        deals: uk.length,
        value: uk.reduce((s, d) => s + (d.dealValueGbpM ?? 0), 0),
      },
      {
        origin: "Overseas buyers",
        deals: all.length - uk.length,
        value: all
          .filter((d) => d.acquirerCountry !== "United Kingdom")
          .reduce((s, d) => s + (d.dealValueGbpM ?? 0), 0),
      },
    ];
  },

  async largestDeals(limit = 8) {
    const all = await source();
    return [...all]
      .sort((a, b) => (b.dealValueGbpM ?? 0) - (a.dealValueGbpM ?? 0))
      .slice(0, limit);
  },

  async advisers(
    filters: { sector?: string | undefined; fromDate?: string | undefined } = {},
  ): Promise<AdviserRow[]> {
    const all = await source();
    const scoped = all.filter(
      (d) =>
        (!filters.sector || filters.sector === "all" || d.sector === filters.sector) &&
        (!filters.fromDate || d.announcementDate >= filters.fromDate),
    );
    const map = new Map<string, { deals: number; value: number }>();
    scoped.forEach((d) => {
      const unique = new Set([...d.targetAdvisers, ...d.buyerAdvisers]);
      unique.forEach((a) => {
        const row = map.get(a) ?? { deals: 0, value: 0 };
        row.deals += 1;
        row.value += d.dealValueGbpM ?? 0;
        map.set(a, row);
      });
    });
    return [...map.entries()]
      .map(([adviser, r]) => ({
        adviser,
        deals: r.deals,
        totalValueGbpM: r.value,
        averageValueGbpM: r.deals ? r.value / r.deals : 0,
      }))
      .sort((a, b) => b.totalValueGbpM - a.totalValueGbpM);
  },

  async facets() {
    const all = await source();
    const uniq = (xs: string[]) => [...new Set(xs)].sort();
    return {
      sectors: uniq(all.map((d) => d.sector)),
      statuses: uniq(all.map((d) => d.status)),
      buyerTypes: uniq(all.map((d) => d.buyerType)),
      advisers: uniq(all.flatMap((d) => [...d.targetAdvisers, ...d.buyerAdvisers])),
    };
  },
};

export const NOT_DISCLOSED = "Not disclosed";

export function formatValue(m: number | null | undefined) {
  if (m == null) return NOT_DISCLOSED;
  if (m >= 1000) return `£${(m / 1000).toFixed(2)}bn`;
  return `£${m.toFixed(0)}m`;
}

export function formatPremium(p: number | null | undefined) {
  return p == null ? NOT_DISCLOSED : `${p.toFixed(1)}%`;
}

export function formatOfferPrice(
  price: number | null | undefined,
  currency?: string | null,
) {
  if (price == null) return NOT_DISCLOSED;
  const code = (currency ?? "GBp").toUpperCase();
  if (code === "GBP") return `£${price.toFixed(2)}`;
  if (code === "GBP" || code === "GBX" || code === "GBp".toUpperCase())
    return `${price.toFixed(0)}p`;
  return `${price.toFixed(2)} ${code}`;
}

export function formatDate(iso: string) {
  return new Date(`${iso}T00:00:00Z`).toLocaleDateString("en-GB", {
    day: "2-digit",
    month: "short",
    year: "numeric",
    timeZone: "UTC",
  });
}
