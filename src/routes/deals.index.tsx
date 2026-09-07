import { createFileRoute } from "@tanstack/react-router";
import { keepPreviousData, useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { Search } from "lucide-react";

import { dealsRepository, type DealQuery } from "@/data/deals";
import { DealsTable } from "@/components/data/deals-table";
import {
  EmptyState,
  ErrorState,
  LoadingRows,
  PageHeader,
  SampleDataNotice,
} from "@/components/data/primitives";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

export const Route = createFileRoute("/deals/")({
  head: () => ({
    meta: [
      { title: "UK M&A Deal Database — UK Deal Pulse" },
      {
        name: "description",
        content:
          "Searchable database of tracked UK public takeovers with filters for sector, deal value, buyer type, adviser and status.",
      },
      { property: "og:title", content: "UK M&A Deal Database — UK Deal Pulse" },
      {
        property: "og:description",
        content: "Search and filter tracked UK public takeover transactions.",
      },
    ],
  }),
  component: DealsPage,
});

const PAGE_SIZE = 8;

function DealsPage() {
  const [query, setQuery] = useState<DealQuery>({
    sort: "newest",
    page: 1,
    pageSize: PAGE_SIZE,
  });

  const facets = useQuery({ queryKey: ["facets"], queryFn: () => dealsRepository.facets() });
  const deals = useQuery({
    queryKey: ["deals", query],
    queryFn: () => dealsRepository.list(query),
    placeholderData: keepPreviousData,
  });

  const update = (patch: Partial<DealQuery>) =>
    setQuery((q) => ({ ...q, ...patch, page: patch.page ?? 1 }));

  const total = deals.data?.total ?? 0;
  const shown = deals.data?.rows.length ?? 0;
  const loadedTo = ((query.page ?? 1) - 1) * PAGE_SIZE + shown;

  return (
    <div className="mx-auto max-w-[1400px] px-4 py-8 sm:px-6">
      <PageHeader
        title="Deal database"
        description="Every transaction tracked by UK Deal Pulse. Search by company or sector, then filter and sort the results."
      />

      <SampleDataNotice className="mt-5" />

      <div className="mt-5 border border-border bg-card">
        <div className="grid grid-cols-1 gap-3 border-b border-border p-4 md:grid-cols-2 xl:grid-cols-4">
          <div className="relative md:col-span-2 xl:col-span-1">
            <Search className="absolute top-1/2 left-2.5 h-3.5 w-3.5 -translate-y-1/2 text-muted-foreground" />
            <Input
              placeholder="Search target, acquirer or sector"
              className="h-9 rounded-none pl-8 text-sm"
              value={query.search ?? ""}
              onChange={(e) => update({ search: e.target.value })}
            />
          </div>

          <Filter
            label="Sector"
            allLabel="All sectors"
            value={query.sector ?? "all"}
            options={facets.data?.sectors ?? []}
            onChange={(v) => update({ sector: v })}
          />
          <Filter
            label="Buyer type"
            allLabel="All buyer types"
            value={query.buyerType ?? "all"}
            options={facets.data?.buyerTypes ?? []}
            onChange={(v) => update({ buyerType: v })}
          />
          <Filter
            label="Status"
            allLabel="All statuses"
            value={query.status ?? "all"}
            options={facets.data?.statuses ?? []}
            onChange={(v) => update({ status: v })}
          />
          <Filter
            label="Adviser"
            allLabel="All advisers"
            value={query.adviser ?? "all"}
            options={facets.data?.advisers ?? []}
            onChange={(v) => update({ adviser: v })}
          />

          <Choice
            label="Minimum deal value"
            value={String(query.minValue ?? 0)}
            options={[
              { value: "0", label: "Any value" },
              { value: "500", label: "£500m+" },
              { value: "1000", label: "£1bn+" },
              { value: "2500", label: "£2.5bn+" },
            ]}
            onChange={(v) => update({ minValue: Number(v) || undefined })}
          />
          <Choice
            label="Announced from"
            value={query.fromDate ?? "any"}
            options={[
              { value: "any", label: "Any date" },
              { value: "2026-01-01", label: "2026 onwards" },
              { value: "2026-06-01", label: "Last 6 months" },
              { value: "2026-08-01", label: "Last 60 days" },
            ]}
            onChange={(v) => update({ fromDate: v === "any" ? undefined : v })}
          />
          <Choice
            label="Sort by"
            value={query.sort ?? "newest"}
            options={[
              { value: "newest", label: "Newest first" },
              { value: "oldest", label: "Oldest first" },
              { value: "largest", label: "Largest deal" },
              { value: "smallest", label: "Smallest deal" },
              { value: "premium-high", label: "Highest premium" },
              { value: "premium-low", label: "Lowest premium" },
            ]}
            onChange={(v) => update({ sort: v as DealQuery["sort"] })}
          />
        </div>

        <div className="p-4">
          {deals.isPending && <LoadingRows rows={8} />}
          {deals.isError && <ErrorState />}
          {deals.data &&
            (deals.data.rows.length ? (
              <DealsTable deals={deals.data.rows} />
            ) : (
              <EmptyState message="No transactions match these filters." />
            ))}
        </div>

        {deals.data && deals.data.rows.length > 0 && (
          <div className="flex flex-wrap items-center justify-between gap-3 border-t border-border px-4 py-3">
            <p className="num text-xs text-muted-foreground">
              Showing {loadedTo} of {total} tracked transactions
            </p>
            <div className="flex gap-2">
              <button
                type="button"
                disabled={(query.page ?? 1) <= 1}
                onClick={() => setQuery((q) => ({ ...q, page: (q.page ?? 1) - 1 }))}
                className="border border-border-strong px-3 py-1.5 text-xs transition-colors hover:bg-muted disabled:opacity-40"
              >
                Previous
              </button>
              <button
                type="button"
                disabled={loadedTo >= total}
                onClick={() => setQuery((q) => ({ ...q, page: (q.page ?? 1) + 1 }))}
                className="border border-border-strong px-3 py-1.5 text-xs transition-colors hover:bg-muted disabled:opacity-40"
              >
                Next
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

function Filter({
  label,
  allLabel,
  value,
  options,
  onChange,
}: {
  label: string;
  allLabel: string;
  value: string;
  options: string[];
  onChange: (v: string) => void;
}) {
  return (
    <Choice
      label={label}
      value={value}
      onChange={onChange}
      options={[
        { value: "all", label: allLabel },
        ...options.map((o) => ({ value: o, label: o })),
      ]}
    />
  );
}

function Choice({
  label,
  value,
  options,
  onChange,
}: {
  label: string;
  value: string;
  options: { value: string; label: string }[];
  onChange: (v: string) => void;
}) {
  return (
    <label className="block">
      <span className="label-caps">{label}</span>
      <Select value={value} onValueChange={onChange}>
        <SelectTrigger className="mt-1 h-9 w-full rounded-none text-sm">
          <SelectValue />
        </SelectTrigger>
        <SelectContent className="rounded-none">
          {options.map((o) => (
            <SelectItem key={o.value} value={o.value} className="text-sm">
              {o.label}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
    </label>
  );
}
