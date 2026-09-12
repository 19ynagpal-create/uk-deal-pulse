import { Link } from "@tanstack/react-router";
import type { Deal } from "@/data/deals";
import { formatDate, formatPremium, formatValue } from "@/data/deals";
import { StatusBadge } from "./primitives";

function standardiseName(name: string) {
  return name.replace(/\s+(plc|PLC|Plc)\s*$/i, " plc");
}

export function DealsTable({
  deals,
  showStatus = true,
}: {
  deals: Deal[];
  showStatus?: boolean;
}) {
  return (
    <>
      {/* Desktop table */}
      <div className="hidden overflow-x-auto md:block">
        <table className="w-full border-collapse text-sm">
          <thead>
            <tr className="border-b border-border-strong text-left">
              <Th className="w-[7.5rem] min-w-[7.5rem]">Announced</Th>
              <Th className="min-w-[11rem] w-[22%]">Target</Th>
              <Th className="min-w-[11rem] w-[22%]">Acquirer</Th>
              <Th className="w-[10rem] min-w-[10rem]">Sector</Th>
              <Th className="w-[7.5rem] min-w-[7.5rem] text-right">Deal value</Th>
              <Th className="w-[6.5rem] min-w-[6.5rem] text-right">Premium</Th>
              <Th className="w-[7rem] min-w-[7rem]">Buyer type</Th>
              {showStatus && <Th className="w-[7.5rem] min-w-[7.5rem]">Status</Th>}
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
                    {standardiseName(deal.target)}
                  </Link>
                </Td>
                <Td className="text-muted-foreground">{standardiseName(deal.acquirer)}</Td>
                <Td className="text-muted-foreground">{deal.sector}</Td>
                <Td className="num whitespace-nowrap text-right font-medium">
                  {formatValue(deal.dealValueGbpM)}
                </Td>
                <Td className="num whitespace-nowrap text-right">
                  {formatPremium(deal.premiumPct)}
                </Td>
                <Td className="text-muted-foreground">
                  {deal.buyerType === "Private Equity" ? "Private equity" : "Strategic"}
                </Td>
                {showStatus && (
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
          <li key={deal.id} className="py-3">
            <Link to="/deals/$dealId" params={{ dealId: deal.id }} className="block">
              <div className="flex items-start justify-between gap-3">
                <div className="min-w-0">
                  <p className="truncate text-sm font-medium">{standardiseName(deal.target)}</p>
                  <p className="mt-0.5 truncate text-xs text-muted-foreground">
                    Acquirer: {standardiseName(deal.acquirer)}
                  </p>
                </div>
                <span className="num shrink-0 whitespace-nowrap text-sm font-semibold">
                  {formatValue(deal.dealValueGbpM)}
                </span>
              </div>
              <div className="mt-2 flex flex-wrap items-center gap-x-4 gap-y-1 text-xs text-muted-foreground">
                <span className="num whitespace-nowrap">{formatDate(deal.announcementDate)}</span>
                <span>{deal.sector}</span>
                <span className="num whitespace-nowrap">Premium {formatPremium(deal.premiumPct)}</span>
                <span>{deal.buyerType === "Private Equity" ? "Private equity" : "Strategic"}</span>
                {showStatus && <StatusBadge status={deal.status} />}
              </div>
            </Link>
          </li>
        ))}
      </ul>
    </>
  );
}

function Th({ children, className = "" }: { children: React.ReactNode; className?: string }) {
  return (
    <th className={`label-caps px-3 py-2 font-semibold ${className}`}>{children}</th>
  );
}

function Td({ children, className = "" }: { children: React.ReactNode; className?: string }) {
  return <td className={`px-3 py-2.5 align-middle ${className}`}>{children}</td>;
}
