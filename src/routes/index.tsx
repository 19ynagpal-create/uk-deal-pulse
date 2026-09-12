import { createFileRoute, Link } from "@tanstack/react-router";
import { useQuery } from "@tanstack/react-query";
import { ArrowRight } from "lucide-react";

import {
  dealsRepository,
  displayName,
  formatDate,
  formatPremium,
  formatValue,
} from "@/data/deals";
import { DealsTable } from "@/components/data/deals-table";
import { CategoryBars, MonthlyBars, MonthlyLine } from "@/components/data/charts";
import {
  EmptyState,
  ErrorState,
  LoadingRows,
  Panel,
  StatCard,
  NoDataNotice,
} from "@/components/data/primitives";

export const Route = createFileRoute("/")({
  head: () => ({
    meta: [
      { title: "UK Deal Pulse — UK public M&A intelligence" },
      {
        name: "description",
        content:
          "Structured intelligence on major UK public takeovers: deal values, premiums, sector activity, buyer types and financial advisers, from primary-source announcements.",
      },
      { property: "og:title", content: "UK Deal Pulse — UK public M&A intelligence" },
      {
        property: "og:description",
        content:
          "Major UK public takeovers, tracked and structured from primary-source announcements.",
      },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary" },
    ],
  }),
  component: Dashboard,
});

function Dashboard() {
  const stats = useQuery({
    queryKey: ["headline-stats"],
    queryFn: () => dealsRepository.headlineStats(),
  });
  const week = useQuery({
    queryKey: ["weekly-summary"],
    queryFn: () => dealsRepository.weeklySummary(),
  });
  const recent = useQuery({
    queryKey: ["deals", "recent"],
    queryFn: () => dealsRepository.list({ pageSize: 8 }),
  });
  const monthly = useQuery({ queryKey: ["by-month"], queryFn: () => dealsRepository.byMonth() });
  const sectors = useQuery({ queryKey: ["by-sector"], queryFn: () => dealsRepository.bySector() });
  const buyers = useQuery({
    queryKey: ["by-buyer-type"],
    queryFn: () => dealsRepository.byBuyerType(),
  });
  const advisers = useQuery({
    queryKey: ["advisers", "top"],
    queryFn: () => dealsRepository.advisers(),
  });

  const isEmpty = stats.data?.dealCount === 0;

  return (
    <div className="mx-auto max-w-[1400px] px-4 py-8 sm:px-6">
      <section className="border-b border-border pb-6">
        <p className="label-caps">
          UK public M&amp;A intelligence, structured from primary-source announcements
        </p>
        <h1 className="mt-2 max-w-3xl text-3xl leading-tight font-semibold sm:text-[2.25rem]">
          Major UK public takeovers, tracked and structured.
        </h1>
        <div className="mt-4 flex flex-wrap items-center gap-x-3 gap-y-3">
          <Link
            to="/deals"
            className="inline-flex items-center gap-2 border border-border-strong bg-primary px-3.5 py-2 text-sm font-medium text-primary-foreground transition-opacity hover:opacity-90"
          >
            Browse the deal database <ArrowRight className="h-3.5 w-3.5" />
          </Link>
          <Link
            to="/methodology"
            className="inline-flex items-center border border-border-strong px-3.5 py-2 text-sm font-medium transition-colors hover:bg-muted"
          >
            Methodology
          </Link>
        </div>
        <dl className="mt-5 flex flex-wrap items-center gap-x-6 gap-y-2 text-xs text-muted-foreground">
          <div className="flex items-center gap-1.5">
            <dt className="label-caps">Tracked transactions</dt>
            <dd className="num font-medium text-foreground">
              {stats.data ? stats.data.dealCount : "—"}
            </dd>
          </div>
          <div className="flex items-center gap-1.5">
            <dt className="label-caps">Last updated</dt>
            <dd className="num font-medium text-foreground">
              {stats.data?.latestAnnouncement
                ? formatDate(stats.data.latestAnnouncement)
                : "—"}
            </dd>
          </div>
          <div className="flex items-center gap-1.5">
            <dt className="label-caps">Sourcing</dt>
            <dd className="font-medium text-foreground">Public primary-source announcements</dd>
          </div>
        </dl>
      </section>

      {isEmpty ? (
        <NoDataNotice className="mt-6" />
      ) : (
      <>

      <section className="mt-6 grid grid-cols-1 gap-3 sm:grid-cols-2 xl:grid-cols-4">
        {stats.isPending && (
          <>
            {Array.from({ length: 4 }).map((_, i) => (
              <div key={i} className="border border-border bg-card px-4 py-6">
                <LoadingRows rows={1} />
              </div>
            ))}
          </>
        )}
        {stats.isError && <div className="sm:col-span-2 xl:col-span-4"><ErrorState /></div>}
        {stats.data && (
          <>
            <StatCard label="Transactions tracked" value={String(stats.data.dealCount)} />
            <StatCard
              label="Total announced deal value"
              value={formatValue(stats.data.totalValueGbpM)}
            />
            <StatCard
              label="Median takeover premium"
              value={formatPremium(stats.data.medianPremiumPct)}
            />
            <StatCard
              label="Deals announced this week"
              value={String(stats.data.dealsThisWeek)}
              sub="Rolling seven-day window"
            />
          </>
        )}
      </section>

      <div className="mt-8 grid grid-cols-1 gap-4 lg:grid-cols-3">
        <Panel
          title="This week in UK M&A"
          note="Rolling seven-day window across tracked transactions"
          className="lg:col-span-1"
        >
          {week.isPending && <LoadingRows rows={5} />}
          {week.isError && <ErrorState />}
          {week.data && (
            <dl className="divide-y divide-border text-sm">
              <Row label="New deals" value={String(week.data.newDeals)} />
              <Row label="Total announced value" value={formatValue(week.data.totalValueGbpM)} />
              <Row
                label="Largest transaction"
                value={week.data.largest ? displayName(week.data.largest.target) : "Not disclosed"}
                sub={week.data.largest ? formatValue(week.data.largest.dealValueGbpM) : undefined}
              />
              <Row label="Median premium" value={formatPremium(week.data.medianPremiumPct)} />
              <Row label="Most active sector" value={week.data.mostActiveSector ?? "—"} />
            </dl>
          )}
          {week.data && week.data.deals.length > 0 && (
            <div className="mt-4 border-t border-border pt-3">
              <p className="label-caps">Latest transactions</p>
              <ul className="mt-2 divide-y divide-border">
                {week.data.deals.map((d) => (
                  <li key={d.id} className="py-2">
                    <Link
                      to="/deals/$dealId"
                      params={{ dealId: d.id }}
                      className="flex items-baseline justify-between gap-3 text-sm hover:underline"
                    >
                      <span className="font-medium">{displayName(d.target)}</span>
                      <span className="num shrink-0 text-xs text-muted-foreground">
                        {formatDate(d.announcementDate)}
                      </span>
                    </Link>
                    <p className="text-xs text-muted-foreground">
                      {displayName(d.acquirer)} · {formatValue(d.dealValueGbpM)}
                    </p>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </Panel>

        <Panel
          title="Recent deals"
          note="Most recently announced tracked transactions"
          className="lg:col-span-2"
          action={
            <Link to="/deals" className="text-xs underline underline-offset-4">
              View all deals
            </Link>
          }
        >
          {recent.isPending && <LoadingRows rows={6} />}
          {recent.isError && <ErrorState />}
          {recent.data &&
            (recent.data.rows.length ? (
              <DealsTable deals={recent.data.rows} />
            ) : (
              <EmptyState message="No transactions recorded yet." />
            ))}
        </Panel>
      </div>

      <div className="mt-4 grid grid-cols-1 gap-4 lg:grid-cols-2">
        <Panel title="UK M&A activity" note="Tracked deals by month">
          {monthly.isPending && <LoadingRows rows={5} />}
          {monthly.isError && <ErrorState />}
          {monthly.data &&
            (monthly.data.length ? (
              <MonthlyBars data={monthly.data} dataKey="deals" name="Tracked deals" />
            ) : (
              <EmptyState message="No monthly activity available." />
            ))}
        </Panel>
        <Panel title="Announced deal value" note="Aggregate announced value by month">
          {monthly.isPending && <LoadingRows rows={5} />}
          {monthly.isError && <ErrorState />}
          {monthly.data && (
            <MonthlyLine
              data={monthly.data.map((m) => ({ month: m.month, value: m.value }))}
              formatter={(v) => formatValue(v)}
            />
          )}
        </Panel>
      </div>

      <div className="mt-4 grid grid-cols-1 gap-4 lg:grid-cols-2">
        <Panel title="Sector activity" note="Deal count by sector">
          {sectors.isPending && <LoadingRows rows={5} />}
          {sectors.isError && <ErrorState />}
          {sectors.data && (
            <CategoryBars data={sectors.data} categoryKey="sector" valueKey="deals" name="Deals" />
          )}
        </Panel>
        <Panel title="Sector value" note="Total announced value by sector">
          {sectors.isPending && <LoadingRows rows={5} />}
          {sectors.isError && <ErrorState />}
          {sectors.data && (
            <CategoryBars
              data={sectors.data}
              categoryKey="sector"
              valueKey="value"
              name="Announced value"
              formatter={(v) => formatValue(v)}
            />
          )}
        </Panel>
      </div>

      <div className="mt-4 grid grid-cols-1 gap-4 lg:grid-cols-2">
        <Panel title="Buyer type" note="Strategic acquirers versus private equity">
          {buyers.isPending && <LoadingRows rows={3} />}
          {buyers.isError && <ErrorState />}
          {buyers.data && (
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-border-strong text-left">
                  <th className="label-caps py-2">Buyer type</th>
                  <th className="label-caps py-2 text-right">Deals</th>
                  <th className="label-caps py-2 text-right">Announced value</th>
                </tr>
              </thead>
              <tbody>
                {buyers.data.map((b) => (
                  <tr key={b.type} className="border-b border-border last:border-0">
                    <td className="py-2.5">{b.type}</td>
                    <td className="num py-2.5 text-right">{b.deals}</td>
                    <td className="num py-2.5 text-right font-medium">{formatValue(b.value)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </Panel>

        <Panel
          title="Top advisers"
          note="Based only on transactions within the UK Deal Pulse dataset"
          action={
            <Link to="/advisers" className="text-xs underline underline-offset-4">
              Full league table
            </Link>
          }
        >
          {advisers.isPending && <LoadingRows rows={5} />}
          {advisers.isError && <ErrorState />}
          {advisers.data && (
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-border-strong text-left">
                  <th className="label-caps py-2">Adviser</th>
                  <th className="label-caps py-2 text-right">Tracked deals</th>
                  <th className="label-caps py-2 text-right">Tracked value</th>
                </tr>
              </thead>
              <tbody>
                {advisers.data.slice(0, 6).map((a) => (
                  <tr key={a.adviser} className="border-b border-border last:border-0">
                    <td className="py-2.5">{a.adviser}</td>
                    <td className="num py-2.5 text-right">{a.deals}</td>
                    <td className="num py-2.5 text-right font-medium">
                      {formatValue(a.totalValueGbpM)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </Panel>
      </div>
      </>
      )}
    </div>
  );
}

function Row({
  label,
  value,
  sub,
}: {
  label: string;
  value: string;
  sub?: string | undefined;
}) {
  return (
    <div className="flex items-baseline justify-between gap-4 py-2.5">
      <dt className="text-muted-foreground">{label}</dt>
      <dd className="text-right font-medium">
        {value}
        {sub && <span className="num block text-xs font-normal text-muted-foreground">{sub}</span>}
      </dd>
    </div>
  );
}
