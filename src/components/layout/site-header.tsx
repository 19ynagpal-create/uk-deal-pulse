import { Link } from "@tanstack/react-router";
import { useState } from "react";
import { Menu, X } from "lucide-react";

const nav = [
  { to: "/", label: "Dashboard" },
  { to: "/deals", label: "Deals" },
  { to: "/analytics", label: "Analytics" },
  { to: "/advisers", label: "Advisers" },
  { to: "/methodology", label: "Methodology" },
] as const;

export function SiteHeader() {
  const [open, setOpen] = useState(false);

  return (
    <header className="sticky top-0 z-50 border-b border-border bg-background/95 backdrop-blur">
      <div className="mx-auto flex h-15 max-w-[1400px] items-center justify-between gap-6 px-4 sm:px-6">
        <Link to="/" className="flex min-w-0 items-baseline gap-2.5">
          <span className="font-serif text-[1.05rem] font-semibold tracking-tight whitespace-nowrap">
            UK Deal Pulse
          </span>
          <span className="hidden truncate border-l border-border pl-2.5 text-[0.7rem] leading-tight text-muted-foreground lg:inline">
            UK public M&amp;A intelligence, structured from primary-source announcements.
          </span>
        </Link>

        <nav className="hidden items-center gap-0.5 md:flex">
          {nav.map((item) => (
            <Link
              key={item.to}
              to={item.to}
              activeOptions={{ exact: item.to === "/" }}
              className="border-b-2 border-transparent px-3 py-4 text-sm whitespace-nowrap text-muted-foreground transition-colors hover:text-foreground"
              activeProps={{
                className: "!border-accent !text-foreground font-semibold",
              }}
            >
              {item.label}
            </Link>
          ))}
        </nav>

        <button
          type="button"
          aria-label="Toggle navigation"
          onClick={() => setOpen((v) => !v)}
          className="inline-flex h-9 w-9 items-center justify-center rounded-sm border border-border md:hidden"
        >
          {open ? <X className="h-4 w-4" /> : <Menu className="h-4 w-4" />}
        </button>
      </div>

      {open && (
        <nav className="border-t border-border bg-background px-4 py-2 md:hidden">
          {nav.map((item) => (
            <Link
              key={item.to}
              to={item.to}
              onClick={() => setOpen(false)}
              className="block border-b border-border/60 py-2.5 text-sm text-muted-foreground last:border-0"
              activeProps={{ className: "!text-foreground font-semibold" }}
              activeOptions={{ exact: item.to === "/" }}
            >
              {item.label}
            </Link>
          ))}
        </nav>
      )}
    </header>
  );
}

export function SiteFooter() {
  return (
    <footer className="mt-16 border-t border-border bg-surface">
      <div className="mx-auto max-w-[1400px] px-4 py-8 text-xs leading-relaxed text-muted-foreground sm:px-6">
        <p className="font-semibold text-foreground">UK Deal Pulse</p>
        <p className="mt-2 max-w-3xl">
          UK Deal Pulse tracks selected major UK public M&amp;A transactions using publicly
          available company announcements and other primary sources. The platform is intended
          for educational and informational purposes and should not be treated as investment
          advice.
        </p>
        <p className="mt-3">
          <Link to="/methodology" className="underline underline-offset-4 hover:text-foreground">
            Methodology and data limitations
          </Link>
        </p>
        <p className="mt-4 text-[0.7rem] text-muted-foreground/80">
          UK Deal Pulse was built and is maintained by Yash Nagpal.
        </p>
      </div>
    </footer>
  );
}
