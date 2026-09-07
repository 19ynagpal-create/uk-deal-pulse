/**
 * DEVELOPMENT SAMPLE DATA
 * -----------------------
 * These records are illustrative placeholders used while the platform is
 * wired up. They are NOT UK Deal Pulse statistics and must be replaced by
 * database-backed records before publication.
 *
 * All access below goes through the async `dealsRepository` functions so the
 * data layer can be swapped for a database client without touching the UI.
 */

export type BuyerType = "Strategic" | "Private Equity";
export type DealStatus = "Announced" | "Recommended" | "Completed" | "Lapsed";

export interface Deal {
  id: string;
  target: string;
  targetTicker?: string;
  acquirer: string;
  acquirerCountry: string;
  sector: string;
  announcementDate: string; // ISO date
  dealValueGbpM: number | null;
  offerPricePence: number | null;
  premiumPct: number | null;
  buyerType: BuyerType;
  status: DealStatus;
  consideration: string | null;
  rationale: string | null;
  financing: string | null;
  targetAdvisers: string[];
  buyerAdvisers: string[];
  sources: { label: string; url: string }[];
}

const rawDeals: Deal[] = [
  {
    id: "sample-anglo-pearl",
    target: "Northgate Industrials plc",
    targetTicker: "NGI.L",
    acquirer: "Pearl Ridge Partners",
    acquirerCountry: "United States",
    sector: "Industrials",
    announcementDate: "2026-09-02",
    dealValueGbpM: 4120,
    offerPricePence: 985,
    premiumPct: 38.4,
    buyerType: "Private Equity",
    status: "Recommended",
    consideration: "Cash",
    rationale:
      "Sample record. The buyer is described as seeking a UK-listed platform in specialist flow-control manufacturing, with the target's board citing a persistent listed-market valuation discount.",
    financing: "Equity from committed funds alongside senior debt facilities.",
    targetAdvisers: ["Rothbury & Co.", "Kingsway Securities"],
    buyerAdvisers: ["Ardenmore Advisory"],
    sources: [{ label: "Rule 2.7 announcement (sample)", url: "https://www.londonstockexchange.com/news" }],
  },
  {
    id: "sample-caledon-vantage",
    target: "Caledon Water Group plc",
    acquirer: "Vantage Infrastructure Holdings",
    acquirerCountry: "Australia",
    sector: "Utilities",
    announcementDate: "2026-08-28",
    dealValueGbpM: 2870,
    offerPricePence: 412,
    premiumPct: 26.1,
    buyerType: "Private Equity",
    status: "Announced",
    consideration: "Cash",
    rationale:
      "Sample record. Long-duration infrastructure buyer acquiring a regulated UK utility asset base.",
    financing: null,
    targetAdvisers: ["Kingsway Securities"],
    buyerAdvisers: ["Halberd Partners", "Rothbury & Co."],
    sources: [{ label: "Company announcement (sample)", url: "https://www.londonstockexchange.com/news" }],
  },
  {
    id: "sample-loxley-mercia",
    target: "Loxley Software plc",
    acquirer: "Mercia Technologies Inc.",
    acquirerCountry: "United States",
    sector: "Technology",
    announcementDate: "2026-08-19",
    dealValueGbpM: 1640,
    offerPricePence: 730,
    premiumPct: 44.9,
    buyerType: "Strategic",
    status: "Recommended",
    consideration: "Cash and shares",
    rationale:
      "Sample record. Strategic acquirer consolidating adjacent enterprise workflow software capability.",
    financing: "Existing cash resources and a new term loan.",
    targetAdvisers: ["Ardenmore Advisory"],
    buyerAdvisers: ["Stanhope Capital Advisers"],
    sources: [{ label: "Offer announcement (sample)", url: "https://www.londonstockexchange.com/news" }],
  },
  {
    id: "sample-brackenhall",
    target: "Brackenhall Retail plc",
    acquirer: "Fernhurst Capital",
    acquirerCountry: "United Kingdom",
    sector: "Consumer",
    announcementDate: "2026-08-06",
    dealValueGbpM: 690,
    offerPricePence: 158,
    premiumPct: 31.7,
    buyerType: "Private Equity",
    status: "Completed",
    consideration: "Cash",
    rationale: "Sample record. Take-private of a mid-cap specialist retailer.",
    financing: null,
    targetAdvisers: ["Kingsway Securities"],
    buyerAdvisers: ["Halberd Partners"],
    sources: [{ label: "Scheme document (sample)", url: "https://www.londonstockexchange.com/news" }],
  },
  {
    id: "sample-orwell-nord",
    target: "Orwell Pharma plc",
    acquirer: "Nordwerk Pharma AG",
    acquirerCountry: "Germany",
    sector: "Healthcare",
    announcementDate: "2026-07-22",
    dealValueGbpM: 3310,
    offerPricePence: 1240,
    premiumPct: 52.3,
    buyerType: "Strategic",
    status: "Announced",
    consideration: "Cash",
    rationale: "Sample record. Pipeline-driven acquisition in specialty therapeutics.",
    financing: "Bridge facility to be refinanced in the bond market.",
    targetAdvisers: ["Rothbury & Co.", "Stanhope Capital Advisers"],
    buyerAdvisers: ["Ardenmore Advisory"],
    sources: [{ label: "Rule 2.7 announcement (sample)", url: "https://www.londonstockexchange.com/news" }],
  },
  {
    id: "sample-tarnbridge",
    target: "Tarnbridge Financial plc",
    acquirer: "Aldgate Mutual",
    acquirerCountry: "United Kingdom",
    sector: "Financials",
    announcementDate: "2026-07-09",
    dealValueGbpM: 1180,
    offerPricePence: 296,
    premiumPct: 18.2,
    buyerType: "Strategic",
    status: "Completed",
    consideration: "Shares",
    rationale: "Sample record. Domestic consolidation of savings and protection books.",
    financing: null,
    targetAdvisers: ["Halberd Partners"],
    buyerAdvisers: ["Kingsway Securities"],
    sources: [{ label: "Company announcement (sample)", url: "https://www.londonstockexchange.com/news" }],
  },
  {
    id: "sample-westmarch",
    target: "Westmarch Energy plc",
    acquirer: "Sable Point Energy Partners",
    acquirerCountry: "Canada",
    sector: "Energy",
    announcementDate: "2026-06-25",
    dealValueGbpM: 2240,
    offerPricePence: 505,
    premiumPct: 22.8,
    buyerType: "Private Equity",
    status: "Announced",
    consideration: "Cash",
    rationale: "Sample record. Acquisition of North Sea and onshore renewables portfolio.",
    financing: null,
    targetAdvisers: ["Stanhope Capital Advisers"],
    buyerAdvisers: ["Rothbury & Co."],
    sources: [{ label: "Offer announcement (sample)", url: "https://www.londonstockexchange.com/news" }],
  },
  {
    id: "sample-halewood",
    target: "Halewood Logistics plc",
    acquirer: "Continental Freight Group",
    acquirerCountry: "Netherlands",
    sector: "Industrials",
    announcementDate: "2026-06-11",
    dealValueGbpM: 845,
    offerPricePence: 214,
    premiumPct: 29.5,
    buyerType: "Strategic",
    status: "Completed",
    consideration: "Cash",
    rationale: "Sample record. European network expansion into UK road freight.",
    financing: "Funded from existing facilities.",
    targetAdvisers: ["Ardenmore Advisory"],
    buyerAdvisers: ["Halberd Partners"],
    sources: [{ label: "Company announcement (sample)", url: "https://www.londonstockexchange.com/news" }],
  },
  {
    id: "sample-pennfield",
    target: "Pennfield Media plc",
    acquirer: "Crestline Media Partners",
    acquirerCountry: "United States",
    sector: "Media",
    announcementDate: "2026-05-28",
    dealValueGbpM: 512,
    offerPricePence: 88,
    premiumPct: 61.4,
    buyerType: "Private Equity",
    status: "Lapsed",
    consideration: "Cash",
    rationale: "Sample record. Offer subsequently lapsed following shareholder opposition.",
    financing: null,
    targetAdvisers: ["Kingsway Securities"],
    buyerAdvisers: ["Stanhope Capital Advisers"],
    sources: [{ label: "Company announcement (sample)", url: "https://www.londonstockexchange.com/news" }],
  },
  {
    id: "sample-gravesend",
    target: "Gravesend Chemicals plc",
    acquirer: "Toyo Speciality Holdings",
    acquirerCountry: "Japan",
    sector: "Materials",
    announcementDate: "2026-05-14",
    dealValueGbpM: 1990,
    offerPricePence: 640,
    premiumPct: 34.2,
    buyerType: "Strategic",
    status: "Completed",
    consideration: "Cash",
    rationale: "Sample record. Vertical integration into speciality chemical intermediates.",
    financing: null,
    targetAdvisers: ["Rothbury & Co."],
    buyerAdvisers: ["Ardenmore Advisory", "Halberd Partners"],
    sources: [{ label: "Scheme document (sample)", url: "https://www.londonstockexchange.com/news" }],
  },
  {
    id: "sample-ashcombe",
    target: "Ashcombe Housing plc",
    acquirer: "Bramwell Real Assets",
    acquirerCountry: "United Kingdom",
    sector: "Real Estate",
    announcementDate: "2026-04-30",
    dealValueGbpM: 1420,
    offerPricePence: 372,
    premiumPct: 15.9,
    buyerType: "Private Equity",
    status: "Completed",
    consideration: "Cash",
    rationale: "Sample record. NAV-discount driven take-private of a listed housing REIT.",
    financing: null,
    targetAdvisers: ["Halberd Partners"],
    buyerAdvisers: ["Kingsway Securities"],
    sources: [{ label: "Company announcement (sample)", url: "https://www.londonstockexchange.com/news" }],
  },
  {
    id: "sample-marloes",
    target: "Marloes Telecom plc",
    acquirer: "Iberia Connect S.A.",
    acquirerCountry: "Spain",
    sector: "Telecommunications",
    announcementDate: "2026-04-16",
    dealValueGbpM: 3760,
    offerPricePence: 149,
    premiumPct: 41.0,
    buyerType: "Strategic",
    status: "Announced",
    consideration: "Cash and shares",
    rationale: "Sample record. Cross-border fixed-line and fibre consolidation.",
    financing: "Rights issue proceeds and committed acquisition facility.",
    targetAdvisers: ["Stanhope Capital Advisers", "Rothbury & Co."],
    buyerAdvisers: ["Ardenmore Advisory"],
    sources: [{ label: "Rule 2.7 announcement (sample)", url: "https://www.londonstockexchange.com/news" }],
  },
  {
    id: "sample-quarrydale",
    target: "Quarrydale Leisure plc",
    acquirer: "Northstar Hospitality",
    acquirerCountry: "United Kingdom",
    sector: "Consumer",
    announcementDate: "2026-03-26",
    dealValueGbpM: 380,
    offerPricePence: 96,
    premiumPct: 27.3,
    buyerType: "Strategic",
    status: "Completed",
    consideration: "Cash",
    rationale: "Sample record. Bolt-on acquisition of a regional leisure estate.",
    financing: null,
    targetAdvisers: ["Kingsway Securities"],
    buyerAdvisers: ["Halberd Partners"],
    sources: [{ label: "Company announcement (sample)", url: "https://www.londonstockexchange.com/news" }],
  },
  {
    id: "sample-eastbrook",
    target: "Eastbrook Insurance plc",
    acquirer: "Granite Harbour Capital",
    acquirerCountry: "United States",
    sector: "Financials",
    announcementDate: "2026-03-05",
    dealValueGbpM: 2610,
    offerPricePence: 458,
    premiumPct: 33.6,
    buyerType: "Private Equity",
    status: "Completed",
    consideration: "Cash",
    rationale: "Sample record. Specialty insurance platform acquisition.",
    financing: null,
    targetAdvisers: ["Ardenmore Advisory"],
    buyerAdvisers: ["Stanhope Capital Advisers"],
    sources: [{ label: "Scheme document (sample)", url: "https://www.londonstockexchange.com/news" }],
  },
  {
    id: "sample-fenwick",
    target: "Fenwick Analytics plc",
    acquirer: "Datamere Group",
    acquirerCountry: "United States",
    sector: "Technology",
    announcementDate: "2026-02-12",
    dealValueGbpM: 960,
    offerPricePence: 1105,
    premiumPct: 47.8,
    buyerType: "Strategic",
    status: "Completed",
    consideration: "Cash",
    rationale: "Sample record. Data infrastructure acquisition to extend UK footprint.",
    financing: null,
    targetAdvisers: ["Rothbury & Co."],
    buyerAdvisers: ["Kingsway Securities"],
    sources: [{ label: "Company announcement (sample)", url: "https://www.londonstockexchange.com/news" }],
  },
  {
    id: "sample-varley",
    target: "Varley Aerospace plc",
    acquirer: "Lockridge Defence Systems",
    acquirerCountry: "United States",
    sector: "Industrials",
    announcementDate: "2026-01-22",
    dealValueGbpM: 5240,
    offerPricePence: 1580,
    premiumPct: 36.1,
    buyerType: "Strategic",
    status: "Completed",
    consideration: "Cash",
    rationale: "Sample record. Defence supply-chain consolidation subject to national-security review.",
    financing: "Cash on balance sheet.",
    targetAdvisers: ["Stanhope Capital Advisers"],
    buyerAdvisers: ["Rothbury & Co.", "Ardenmore Advisory"],
    sources: [{ label: "Rule 2.7 announcement (sample)", url: "https://www.londonstockexchange.com/news" }],
  },
];

export const IS_SAMPLE_DATA = true;

const byDateDesc = (a: Deal, b: Deal) =>
  b.announcementDate.localeCompare(a.announcementDate);

/** Simulated async boundary so a database client can drop in unchanged. */
async function source(): Promise<Deal[]> {
  return [...rawDeals].sort(byDateDesc);
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
    const all = await source();
    return all.find((d) => d.id === id) ?? null;
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
    let deals = all.filter((d) => d.announcementDate >= windowStart);
    // Sample dataset fallback: show the most recent records when the rolling
    // seven-day window is empty, clearly labelled in the UI.
    if (!deals.length) deals = all.slice(0, 3);
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
    const map = new Map<string, { sector: string; deals: number; value: number; premiums: number[] }>();
    all.forEach((d) => {
      const row = map.get(d.sector) ?? { sector: d.sector, deals: 0, value: 0, premiums: [] };
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
        medianPremium: median(r.premiums) ?? 0,
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
      { origin: "UK buyers", deals: uk.length, value: uk.reduce((s, d) => s + (d.dealValueGbpM ?? 0), 0) },
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

  async advisers(filters: { sector?: string | undefined; fromDate?: string | undefined } = {}): Promise<AdviserRow[]> {
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

export function formatPence(p: number | null | undefined) {
  return p == null ? NOT_DISCLOSED : `${p.toFixed(0)}p`;
}

export function formatDate(iso: string) {
  return new Date(`${iso}T00:00:00Z`).toLocaleDateString("en-GB", {
    day: "2-digit",
    month: "short",
    year: "numeric",
    timeZone: "UTC",
  });
}
