import { Link } from "@tanstack/react-router";
import type { Deal } from "@/data/deals";
import { displayName, formatDate, formatPremium, formatValue } from "@/data/deals";
import { StatusBadge } from "./primitives";

export function DealsTable({
  deals,
  showStatus = true,
  compact = false,
}: {
  deals: Deal[];
  showStatus?: boolean;
  compact?: boolean;
}) {
  const withStatus = showStatus && !compact;
  return (
    <>
      {/* Desktop table */}
      <div className="-mx-4 hidden overflow-x-auto px-4 md:block">
        <table
          className={`w-full border-collapse text-sm ${compact ? "min-w-[40rem]" : withStatus ? "min-w-[56rem]" : "min-w-[46rem]"}`}
        >
          <thead>
            <tr className="border-b border-border-strong text-left">
              <Th className="w-[6.5rem] min-w-[6.5rem]">Announced</Th>
              <Th className={`w-[24%] ${compact ? "min-w-[10.5rem]" : "min-w-[13.5rem]"}`}>
                Target
              </Th>
              <Th className={`w-[24%] ${compact ? "min-w-[10.5rem]" : "min-w-[13.5rem]"}`}>
                Acquirer
              </Th>
              <Th className={compact ? "w-[7.5rem] min-w-[7.5rem]" : "w-[9rem] min-w-[9rem]"}>
                Sector
              </Th>
              <Th className="w-[7.5rem] min-w-[7.5rem] text-right">Deal value</Th>
              {!compact && <Th className="w-[7rem] min-w-[7rem] text-right">Premium</Th>}
              {!compact && <Th className="w-[6.5rem] min-w-[6.5rem]">Buyer type</Th>}
              {withStatus && <Th className="w-[7rem] min-w-[7rem]">Status</Th>}
            </tr>
          </thead>
          <tbody>
            {deals.map((deal) => (
              <tr
                key={deal.id}
                className="border-b border-border transition-colors last:border-0 hover:bg-muted/60"
              >
                <Td className="num whitespace-nowrap text-muted-foreground">
                  {formatDate(deal.announcementDate)}
                </Td>
                <Td>
                  <Link
                    to="/deals/$dealId"
                    params={{ dealId: deal.id }}
                    className="font-medium underline-offset-4 hover:underline"
                  >
                    {displayName(deal.target)}
                  </Link>
                </Td>
                <Td className="text-muted-foreground">{displayName(deal.acquirer)}</Td>
                <Td className="text-muted-foreground">{deal.sector}</Td>
                <Td className="num whitespace-nowrap text-right font-medium tabular-nums">
                  {formatValue(deal.dealValueGbpM)}
                </Td>
                {!compact && (
                  <Td className="num whitespace-nowrap text-right tabular-nums">
                    {formatPremium(deal.premiumPct)}
                  </Td>
                )}
                {!compact && (
                  <Td className="whitespace-nowrap text-muted-foreground">
                    {deal.buyerType === "Private Equity" ? "Private equity" : "Strategic"}
                  </Td>
                )}
                {withStatus && (
                  <Td>
                    <StatusBadge status={deal.status} />
                  </Td>
                )}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Mobile cards */}
      <ul className="divide-y divide-border md:hidden">
        {deals.map((deal) => (
          <li key={deal.id} className="py-3.5 first:pt-1">
            <Link to="/deals/$dealId" params={{ dealId: deal.id }} className="block">
              <div className="flex items-start justify-between gap-3">
                <div className="min-w-0">
                  <p className="truncate text-sm font-medium">{displayName(deal.target)}</p>
                  <p className="mt-0.5 truncate text-xs text-muted-foreground">
                    Acquirer: {displayName(deal.acquirer)}
                  </p>
                </div>
                <span className="num shrink-0 whitespace-nowrap text-sm font-semibold tabular-nums">
                  {formatValue(deal.dealValueGbpM)}
                </span>
              </div>
              <div className="mt-2 flex flex-wrap items-center gap-x-3.5 gap-y-1.5 text-xs text-muted-foreground">
                <span className="num whitespace-nowrap">{formatDate(deal.announcementDate)}</span>
                <span>{deal.sector}</span>
                <span className="num whitespace-nowrap">
                  Premium {formatPremium(deal.premiumPct)}
                </span>
                <span>{deal.buyerType === "Private Equity" ? "Private equity" : "Strategic"}</span>
                {withStatus && <StatusBadge status={deal.status} />}
              </div>
            </Link>
          </li>
        ))}
      </ul>
    </>
  );
}

function Th({ children, className = "" }: { children: React.ReactNode; className?: string }) {
  return <th className={`label-caps px-3 py-2.5 font-semibold ${className}`}>{children}</th>;
}

function Td({ children, className = "" }: { children: React.ReactNode; className?: string }) {
  return <td className={`px-3 py-3 align-middle ${className}`}>{children}</td>;
}
