import { createFileRoute, Link } from "@tanstack/react-router";
import { useQuery } from "@tanstack/react-query";
import { ArrowLeft, ExternalLink } from "lucide-react";

import {
  dealsRepository,
  displayName,
  formatDate,
  formatOfferPrice,
  formatPremium,
  formatValue,
  NOT_DISCLOSED,
} from "@/data/deals";
import {
  ErrorState,
  LoadingRows,
  Panel,
  StatCard,
  StatusBadge,
} from "@/components/data/primitives";

export const Route = createFileRoute("/deals/$dealId")({
  head: () => ({
    meta: [
      { title: "Transaction detail — UK Deal Pulse" },
      {
        name: "description",
        content:
          "Transaction detail for a tracked UK public takeover: deal value, offer price, premium, advisers, financing and sources.",
      },
      { property: "og:title", content: "Transaction detail — UK Deal Pulse" },
      {
        property: "og:description",
        content: "Deal value, premium, advisers, financing and sources for a tracked UK takeover.",
      },
      { property: "og:type", content: "article" },
      { name: "twitter:card", content: "summary" },
    ],
  }),
  component: DealDetail,
});

function DealDetail() {
  const { dealId } = Route.useParams();
  const deal = useQuery({
    queryKey: ["deal", dealId],
    queryFn: () => dealsRepository.getById(dealId),
  });

  return (
    <div className="mx-auto max-w-[1100px] px-4 py-8 sm:px-6">
      <Link
        to="/deals"
        className="inline-flex items-center gap-1.5 text-xs text-muted-foreground hover:text-foreground"
      >
        <ArrowLeft className="h-3.5 w-3.5" /> Back to deal database
      </Link>

      {deal.isPending && (
        <div className="mt-6">
          <LoadingRows rows={8} />
        </div>
      )}
      {deal.isError && (
        <div className="mt-6">
          <ErrorState />
        </div>
      )}
      {deal.data === null && (
        <div className="mt-6 border border-border bg-card px-4 py-10 text-center text-sm text-muted-foreground">
          This transaction is not in the tracked dataset.
        </div>
      )}

      {deal.data && (
        <article className="mt-4">
          <header className="border-b border-border pb-5">
            <div className="flex flex-wrap items-center gap-2">
              <StatusBadge status={deal.data.status} />
              <span className="text-xs text-muted-foreground">{deal.data.sector}</span>
            </div>
            <h1 className="mt-3 text-2xl leading-snug font-semibold sm:text-3xl">
              {displayName(deal.data.target)} acquired by {displayName(deal.data.acquirer)}
            </h1>
          </header>


          <div className="mt-5 grid grid-cols-2 gap-3 xl:grid-cols-5">
            <StatCard label="Deal value" value={formatValue(deal.data.dealValueGbpM)} />
            <StatCard label="Offer price" value={formatOfferPrice(deal.data.offerPrice, deal.data.offerPriceCurrency)} />
            <StatCard label="Takeover premium" value={formatPremium(deal.data.premiumPct)} />
            <StatCard label="Announced" value={formatDate(deal.data.announcementDate)} />
            <StatCard label="Status" value={deal.data.status} />
          </div>

          <div className="mt-4 grid grid-cols-1 gap-4 lg:grid-cols-2">
            <Panel title="Transaction overview">
              <dl className="divide-y divide-border text-sm">
                <Detail label="Target" value={displayName(deal.data.target)} />
                <Detail label="Acquirer" value={displayName(deal.data.acquirer)} />
                <Detail label="Sector" value={deal.data.sector} />
                <Detail
                  label="Buyer type"
                  value={deal.data.buyerType === "Private Equity" ? "Private equity" : "Strategic"}
                />
                <Detail label="Acquirer country" value={deal.data.acquirerCountry} />
                <Detail label="Offer type" value={deal.data.offerType ?? NOT_DISCLOSED} />
              </dl>
            </Panel>

            <Panel title="Strategic rationale">
              <p className="text-sm leading-relaxed text-muted-foreground">
                {deal.data.rationale ?? NOT_DISCLOSED}
              </p>
            </Panel>

            <Panel title="Advisers" note="As disclosed in the transaction announcement">
              <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                <AdviserList title="Target financial advisers" items={deal.data.targetAdvisers} />
                <AdviserList title="Buyer financial advisers" items={deal.data.buyerAdvisers} />
              </div>
            </Panel>

            <Panel title="Financing">
              <p className="text-sm leading-relaxed text-muted-foreground">
                {deal.data.financing ?? NOT_DISCLOSED}
              </p>
            </Panel>

            <Panel title="Sources" className="lg:col-span-2">
              {deal.data.sources.length ? (
                <ul className="space-y-2 text-sm">
                  {deal.data.sources.map((s) => (
                    <li key={s.url}>
                      <a
                        href={s.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="inline-flex items-center gap-1.5 underline underline-offset-4 hover:text-accent"
                      >
                        {s.label} <ExternalLink className="h-3.5 w-3.5" />
                      </a>
                    </li>
                  ))}
                </ul>
              ) : (
                <p className="text-sm text-muted-foreground">{NOT_DISCLOSED}</p>
              )}
            </Panel>
          </div>
        </article>
      )}
    </div>
  );
}

function Detail({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-baseline justify-between gap-4 py-2.5">
      <dt className="text-muted-foreground">{label}</dt>
      <dd className="text-right font-medium">{value}</dd>
    </div>
  );
}

function AdviserList({ title, items }: { title: string; items: string[] }) {
  return (
    <div>
      <p className="label-caps">{title}</p>
      {items.length ? (
        <ul className="mt-2 space-y-1 text-sm">
          {items.map((a) => (
            <li key={a}>{a}</li>
          ))}
        </ul>
      ) : (
        <p className="mt-2 text-sm text-muted-foreground">{NOT_DISCLOSED}</p>
      )}
    </div>
  );
}
