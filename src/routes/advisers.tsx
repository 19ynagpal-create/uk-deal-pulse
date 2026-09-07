import { createFileRoute } from "@tanstack/react-router";
import { useQuery } from "@tanstack/react-query";
import { useState } from "react";

import { dealsRepository, formatValue } from "@/data/deals";
import {
  EmptyState,
  ErrorState,
  LoadingRows,
  PageHeader,
} from "@/components/data/primitives";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

export const Route = createFileRoute("/advisers")({
  head: () => ({
    meta: [
      { title: "Adviser League Table — UK Deal Pulse" },
      {
        name: "description",
        content:
          "Financial advisers ranked by tracked UK public takeover deal count and value within the UK Deal Pulse dataset.",
      },
      { property: "og:title", content: "Adviser League Table — UK Deal Pulse" },
      {
        property: "og:description",
        content: "Advisers appearing most frequently across tracked UK takeovers.",
      },
    ],
  }),
  component: AdvisersPage,
});

function AdvisersPage() {
  const [sector, setSector] = useState("all");
  const [period, setPeriod] = useState("all");

  const facets = useQuery({ queryKey: ["facets"], queryFn: () => dealsRepository.facets() });
  const advisers = useQuery({
    queryKey: ["advisers", sector, period],
    queryFn: () =>
      dealsRepository.advisers({
        sector,
        fromDate: period === "all" ? undefined : period,
      }),
  });

  return (
    <div className="mx-auto max-w-[1100px] px-4 py-8 sm:px-6">
      <PageHeader
        title="Adviser league table"
        description="Financial advisers ranked by their appearances across tracked transactions."
      />

      <div className="mt-5 border border-border-strong border-l-4 border-l-primary bg-surface px-4 py-2.5 text-xs leading-relaxed text-muted-foreground">
        <span className="font-semibold text-foreground">Dataset scope.</span> This table is based
        only on transactions within the UK Deal Pulse dataset. It is not an official industry
        league table and should not be read as one.
      </div>


      <div className="mt-5 border border-border bg-card">
        <div className="grid grid-cols-1 gap-3 border-b border-border p-4 sm:grid-cols-2">
          <label className="block">
            <span className="label-caps">Time period</span>
            <Select value={period} onValueChange={setPeriod}>
              <SelectTrigger className="mt-1 h-9 w-full rounded-none text-sm">
                <SelectValue />
              </SelectTrigger>
              <SelectContent className="rounded-none">
                <SelectItem value="all">All tracked periods</SelectItem>
                <SelectItem value="2026-01-01">2026 onwards</SelectItem>
                <SelectItem value="2026-06-01">Last 6 months</SelectItem>
                <SelectItem value="2026-08-01">Last 60 days</SelectItem>
              </SelectContent>
            </Select>
          </label>
          <label className="block">
            <span className="label-caps">Sector</span>
            <Select value={sector} onValueChange={setSector}>
              <SelectTrigger className="mt-1 h-9 w-full rounded-none text-sm">
                <SelectValue />
              </SelectTrigger>
              <SelectContent className="rounded-none">
                <SelectItem value="all">All sectors</SelectItem>
                {(facets.data?.sectors ?? []).map((s) => (
                  <SelectItem key={s} value={s}>
                    {s}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </label>
        </div>

        <div className="p-4">
          {advisers.isPending && <LoadingRows rows={6} />}
          {advisers.isError && <ErrorState />}
          {advisers.data &&
            (advisers.data.length ? (
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-border-strong text-left">
                      <th className="label-caps py-2 pr-3">#</th>
                      <th className="label-caps py-2">Adviser</th>
                      <th className="label-caps py-2 text-right">Tracked deals</th>
                      <th className="label-caps py-2 text-right">Total tracked value</th>
                      <th className="label-caps py-2 text-right">Average deal size</th>
                    </tr>
                  </thead>
                  <tbody>
                    {advisers.data.map((a, i) => (
                      <tr key={a.adviser} className="border-b border-border last:border-0">
                        <td className="num py-2.5 pr-3 text-muted-foreground">{i + 1}</td>
                        <td className="py-2.5 font-medium">{a.adviser}</td>
                        <td className="num py-2.5 text-right">{a.deals}</td>
                        <td className="num py-2.5 text-right font-medium">
                          {formatValue(a.totalValueGbpM)}
                        </td>
                        <td className="num py-2.5 text-right">
                          {formatValue(a.averageValueGbpM)}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <EmptyState message="No advisers match these filters." />
            ))}
        </div>
      </div>
    </div>
  );
}
