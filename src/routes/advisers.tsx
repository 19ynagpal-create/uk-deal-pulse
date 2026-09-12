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
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary" },
    ],
  }),
  component: AdvisersPage,
});

const DEFAULT_VISIBLE = 10;

function AdvisersPage() {
  const [sector, setSector] = useState("all");
  const [period, setPeriod] = useState("all");
  const [showAll, setShowAll] = useState(false);

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

      <p className="mt-4 border-l-2 border-border-strong pl-3 text-[0.7rem] leading-relaxed text-muted-foreground">
        Dataset scope: based only on transactions within the UK Deal Pulse dataset. Not an official
        industry league table.
      </p>




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
              <>
                <div className="-mx-4 overflow-x-auto px-4">
                  <table className="w-full min-w-[38rem] text-sm">
                    <thead>
                      <tr className="border-b border-border-strong text-left">
                        <th className="label-caps w-10 py-2.5 pr-3">#</th>
                        <th className="label-caps py-2.5">Adviser</th>
                        <th className="label-caps py-2.5 pl-6 text-right whitespace-nowrap">
                          Tracked deals
                        </th>
                        <th className="label-caps py-2.5 pl-6 text-right whitespace-nowrap">
                          Total tracked value
                        </th>
                        <th className="label-caps py-2.5 pl-6 text-right whitespace-nowrap">
                          Average deal size
                        </th>
                      </tr>
                    </thead>
                    <tbody>
                      {(showAll ? advisers.data : advisers.data.slice(0, DEFAULT_VISIBLE)).map(
                        (a, i) => (
                          <tr
                            key={a.adviser}
                            className="border-b border-border transition-colors last:border-0 hover:bg-muted/60"
                          >
                            <td className="num py-3 pr-3 text-muted-foreground tabular-nums">
                              {i + 1}
                            </td>
                            <td className="py-3 pr-4 font-medium">{a.adviser}</td>
                            <td className="num py-3 pl-6 text-right tabular-nums">{a.deals}</td>
                            <td className="num py-3 pl-6 text-right font-medium whitespace-nowrap tabular-nums">
                              {formatValue(a.totalValueGbpM)}
                            </td>
                            <td className="num py-3 pl-6 text-right whitespace-nowrap tabular-nums">
                              {formatValue(a.averageValueGbpM)}
                            </td>
                          </tr>
                        ),
                      )}
                    </tbody>
                  </table>
                </div>
                {advisers.data.length > DEFAULT_VISIBLE && (
                  <div className="mt-4 flex flex-wrap items-center justify-between gap-3 border-t border-border pt-3">
                    <p className="text-xs text-muted-foreground">
                      Showing{" "}
                      <span className="num text-foreground">
                        {showAll ? advisers.data.length : DEFAULT_VISIBLE}
                      </span>{" "}
                      of <span className="num text-foreground">{advisers.data.length}</span>{" "}
                      advisers
                    </p>
                    <button
                      type="button"
                      onClick={() => setShowAll((v) => !v)}
                      className="border border-border-strong px-3 py-1.5 text-xs font-medium transition-colors hover:bg-muted"
                    >
                      {showAll ? "Show top 10" : "View all advisers"}
                    </button>
                  </div>
                )}
              </>
            ) : (
              <EmptyState message="No advisers match these filters." />
            ))}
        </div>
      </div>
    </div>
  );
}
