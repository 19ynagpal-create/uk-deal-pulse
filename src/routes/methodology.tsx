import { createFileRoute } from "@tanstack/react-router";
import { PageHeader } from "@/components/data/primitives";

export const Route = createFileRoute("/methodology")({
  head: () => ({
    meta: [
      { title: "Methodology — UK Deal Pulse" },
      {
        name: "description",
        content:
          "How UK Deal Pulse selects, sources, extracts and validates UK public M&A transaction data, plus coverage limits and disclaimer.",
      },
      { property: "og:title", content: "Methodology — UK Deal Pulse" },
      {
        property: "og:description",
        content: "Coverage, data sources, AI-assisted extraction, limitations and disclaimer.",
      },
    ],
  }),
  component: MethodologyPage,
});

function MethodologyPage() {
  return (
    <div className="mx-auto max-w-[820px] px-4 py-8 sm:px-6">
      <PageHeader title="Methodology" />

      <p className="mt-6 border-l-2 border-accent pl-4 text-[0.95rem] leading-relaxed">
        UK Deal Pulse tracks selected major UK public M&amp;A transactions using publicly available
        company announcements and other primary sources. AI-assisted extraction is used to
        structure transaction information. Data is validated using defined checks before
        publication. The platform is intended for educational and informational purposes and
        should not be treated as investment advice.
      </p>

      <Section title="Coverage">
        <p>
          Coverage focuses on major takeovers of UK-listed companies, including recommended and
          hostile offers, schemes of arrangement and contractual offers. Smaller transactions,
          private company deals and minority stake purchases are generally out of scope. The
          dataset is selective rather than exhaustive: absence of a transaction does not mean it
          did not occur.
        </p>
      </Section>

      <Section title="Data sources">
        <ul>
          <li>Regulatory announcements published by the companies involved</li>
          <li>Scheme documents and offer documents</li>
          <li>Company investor relations releases and presentations</li>
          <li>Other primary public filings referenced on each transaction page</li>
        </ul>
        <p>
          Each transaction page lists the original public sources used so figures can be checked
          against the underlying documents.
        </p>
      </Section>

      <Section title="AI-assisted extraction">
        <p>
          Transaction announcements are long and inconsistently structured. AI-assisted extraction
          is used to convert them into structured fields such as deal value, offer price, premium,
          consideration structure, adviser names and financing arrangements. Extraction is a
          drafting aid, not the final record.
        </p>
        <p>
          Extracted values pass defined checks before publication, including consistency between
          offer price and stated premium, plausibility ranges for deal value, date validation, and
          confirmation that every published field can be traced to a cited source. Fields that
          cannot be verified are recorded as &ldquo;Not disclosed&rdquo; rather than estimated.
        </p>
      </Section>

      <Section title="Data limitations">
        <ul>
          <li>Announced values reflect figures at announcement and are not restated later.</li>
          <li>
            Premiums depend on the reference price chosen in the announcement, which varies between
            transactions.
          </li>
          <li>Currency conversion, where applied, uses rates at the announcement date.</li>
          <li>
            Adviser tables count appearances within this dataset only and are not official league
            tables.
          </li>
          <li>Transaction status can change after publication; records are updated weekly.</li>
        </ul>
      </Section>

      <Section title="Disclaimer">
        <p>
          UK Deal Pulse is an informational and educational resource. It does not provide
          investment advice, and nothing on this site is a recommendation to buy or sell any
          security. Figures may contain errors or omissions. Always consult the original public
          documents before relying on any number shown here.
        </p>
      </Section>
    </div>
  );
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <section className="mt-8 border-t border-border pt-6">
      <h2 className="text-lg font-semibold">{title}</h2>
      <div className="mt-3 space-y-3 text-sm leading-relaxed text-muted-foreground [&_li]:mt-1.5 [&_ul]:list-disc [&_ul]:pl-5">
        {children}
      </div>
    </section>
  );
}
