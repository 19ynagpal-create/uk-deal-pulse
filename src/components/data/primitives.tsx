import type { ReactNode } from "react";
import { cn } from "@/lib/utils";
import { Skeleton } from "@/components/ui/skeleton";
import type { DealStatus, BuyerType } from "@/data/deals";

export function PageHeader({
  title,
  description,
  children,
}: {
  title: string;
  description?: string;
  children?: ReactNode;
}) {
  return (
    <div className="border-b border-border pb-5">
      <h1 className="text-2xl font-semibold sm:text-[1.75rem]">{title}</h1>
      {description && (
        <p className="mt-2 max-w-3xl text-sm leading-relaxed text-muted-foreground">
          {description}
        </p>
      )}
      {children}
    </div>
  );
}

export function Panel({
  title,
  note,
  action,
  children,
  className,
}: {
  title: string;
  note?: string;
  action?: ReactNode;
  children: ReactNode;
  className?: string;
}) {
  return (
    <section className={cn("border border-border bg-card", className)}>
      <div className="flex flex-wrap items-center justify-between gap-2 border-b border-border px-4 py-3">
        <div>
          <h2 className="text-sm font-semibold tracking-tight">{title}</h2>
          {note && <p className="mt-0.5 text-xs text-muted-foreground">{note}</p>}
        </div>
        {action}
      </div>
      <div className="p-4">{children}</div>
    </section>
  );
}

export function StatCard({
  label,
  value,
  sub,
}: {
  label: string;
  value: string;
  sub?: string;
}) {
  return (
    <div className="border border-border bg-card px-4 py-3.5">
      <p className="label-caps">{label}</p>
      <p className="num mt-2 text-[1.6rem] leading-none font-semibold">{value}</p>
      {sub && <p className="mt-2 text-xs text-muted-foreground">{sub}</p>}
    </div>
  );
}

export function SampleDataNotice({ className }: { className?: string }) {
  return (
    <div
      className={cn(
        "border border-border-strong border-l-4 border-l-accent bg-surface px-4 py-2.5 text-xs leading-relaxed text-muted-foreground",
        className,
      )}
    >
      <span className="font-semibold text-foreground">Development sample data.</span>{" "}
      All figures shown are illustrative placeholder records used during build. They are not
      UK Deal Pulse statistics and will be replaced by validated database records.
    </div>
  );
}

export function StatusBadge({ status }: { status: DealStatus }) {
  const tone: Record<DealStatus, string> = {
    Announced: "border-border-strong text-foreground",
    Recommended: "border-accent/50 text-accent",
    Completed: "border-positive/40 text-positive",
    Lapsed: "border-destructive/40 text-destructive",
  };
  return (
    <span
      className={cn(
        "inline-flex items-center border px-1.5 py-0.5 text-[0.68rem] font-medium",
        tone[status],
      )}
    >
      {status}
    </span>
  );
}

export function BuyerTypeTag({ type }: { type: BuyerType }) {
  return (
    <span className="text-xs text-muted-foreground">
      {type === "Private Equity" ? "Private equity" : "Strategic"}
    </span>
  );
}

export function EmptyState({ message }: { message: string }) {
  return (
    <div className="border border-dashed border-border-strong px-4 py-10 text-center text-sm text-muted-foreground">
      {message}
    </div>
  );
}

export function ErrorState({ message }: { message?: string }) {
  return (
    <div className="border border-destructive/40 bg-card px-4 py-6 text-sm text-destructive">
      {message ?? "This data could not be loaded. Please try again."}
    </div>
  );
}

export function LoadingRows({ rows = 5 }: { rows?: number }) {
  return (
    <div className="space-y-2">
      {Array.from({ length: rows }).map((_, i) => (
        <Skeleton key={i} className="h-9 w-full rounded-none" />
      ))}
    </div>
  );
}
