import { createFileRoute, Link } from "@tanstack/react-router";
import { useQuery } from "@tanstack/react-query";

import { dealsRepository, formatPremium, formatValue } from "@/data/deals";
import { CategoryBars, MonthlyBars, MonthlyLine } from "@/components/data/charts";
import {
  ErrorState,
  LoadingRows,
  PageHeader,
  Panel,
} from "@/components/data/primitives";

export const Route = createFileRoute("/analytics")({
  head: () => ({
    meta: [
      { title: "UK M&A Analytics — UK Deal Pulse" },
      {
        name: "description",
        content:
          "Charts on UK takeover activity: deal volume and value over time, sector activity, median premiums, buyer types and largest transactions.",
      },
      { property: "og:title", content: "UK M&A Analytics — UK Deal Pulse" },
      {
        property: "og:description",
        content: "Deal activity, sector mix, premiums and buyer composition across tracked UK takeovers.",
      },
    ],
  }),
  component: AnalyticsPage,
});

function AnalyticsPage() {
  const monthly = useQuery({ queryKey: ["by-month"], queryFn: () => dealsRepository.byMonth() });
  const sectors = useQuery({ queryKey: ["by-sector"], queryFn: () => dealsRepository.bySector() });
  const buyers = useQuery({
    queryKey: ["by-buyer-type"],
    queryFn: () => dealsRepository.byBuyerType(),
  });
  const origin = useQuery({
    queryKey: ["by-origin"],
    queryFn: () => dealsRepository.byBuyerOrigin(),
  });
  const largest = useQuery({
    queryKey: ["largest"],
    queryFn: () => dealsRepository.largestDeals(8),
  });

  const state = (q: { isPending: boolean; isError: boolean }) =>
    q.isPending ? <LoadingRows rows={5} /> : q.isError ? <ErrorState /> : null;

  return (
    <div className="mx-auto max-w-[1400px] px-4 py-8 sm:px-6">
      <PageHeader
        title="Analytics"
        description="Aggregate views of tracked UK public takeover activity. All figures are derived from records in the UK Deal Pulse dataset."
      />


      <div className="mt-5 grid grid-cols-1 gap-4 lg:grid-cols-2">
        <Panel title="Deal activity over time" note="Tracked transactions by month">
          {state(monthly) ??
            (monthly.data && <MonthlyBars data={monthly.data} dataKey="deals" name="Tracked deals" />)}
        </Panel>

        <Panel title="Total deal value over time" note="Announced value by month">
          {state(monthly) ??
            (monthly.data && (
              <MonthlyLine
                data={monthly.data.map((m) => ({ month: m.month, value: m.value }))}
                formatter={(v) => formatValue(v)}
              />
            ))}
        </Panel>

        <Panel title="Deal activity by sector" note="Number of tracked transactions">
          {state(sectors) ??
            (sectors.data && (
              <CategoryBars data={sectors.data} categoryKey="sector" valueKey="deals" name="Deals" />
            ))}
        </Panel>

        <Panel title="Median premium by sector" note="Median takeover premium, tracked deals">
          {state(sectors) ??
            (sectors.data && (
              <CategoryBars
                data={sectors.data
                  .filter((s) => s.medianPremiumPct != null)
                  .map((s) => ({ ...s, medianPremiumPct: s.medianPremiumPct as number }))
                  .sort((a, b) => b.medianPremiumPct - a.medianPremiumPct)}
                categoryKey="sector"
                valueKey="medianPremiumPct"
                name="Median premium"
                formatter={(v) => `${v.toFixed(0)}%`}
              />
            ))}
        </Panel>

        <Panel title="Strategic versus private equity buyers" note="Announced value by buyer type">
          {state(buyers) ??
            (buyers.data && (
              <CategoryBars
                data={buyers.data}
                categoryKey="type"
                valueKey="value"
                name="Announced value"
                formatter={(v) => formatValue(v)}
                height={200}
                colorful
              />
            ))}
        </Panel>

        <Panel title="Foreign versus UK buyers" note="Announced value by acquirer domicile">
          {state(origin) ??
            (origin.data && (
              <CategoryBars
                data={origin.data}
                categoryKey="origin"
                valueKey="value"
                name="Announced value"
                formatter={(v) => formatValue(v)}
                height={200}
                colorful
              />
            ))}
        </Panel>

        <Panel title="Largest transactions" note="By announced deal value" className="lg:col-span-2">
          {state(largest) ??
            (largest.data && (
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-border-strong text-left">
                      <th className="label-caps py-2">Target</th>
                      <th className="label-caps py-2">Acquirer</th>
                      <th className="label-caps py-2">Sector</th>
                      <th className="label-caps py-2 text-right">Deal value</th>
                      <th className="label-caps py-2 text-right">Premium</th>
                    </tr>
                  </thead>
                  <tbody>
                    {largest.data.map((d) => (
                      <tr key={d.id} className="border-b border-border last:border-0">
                        <td className="py-2.5">
                          <Link
                            to="/deals/$dealId"
                            params={{ dealId: d.id }}
                            className="font-medium underline-offset-4 hover:underline"
                          >
                            {d.target}
                          </Link>
                        </td>
                        <td className="py-2.5 text-muted-foreground">{d.acquirer}</td>
                        <td className="py-2.5 text-muted-foreground">{d.sector}</td>
                        <td className="num py-2.5 text-right font-medium">
                          {formatValue(d.dealValueGbpM)}
                        </td>
                        <td className="num py-2.5 text-right">{formatPremium(d.premiumPct)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ))}
        </Panel>
      </div>
    </div>
  );
}
