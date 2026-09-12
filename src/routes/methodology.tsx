import { createFileRoute } from "@tanstack/react-router";
import { PageHeader } from "@/components/data/primitives";

export const Route = createFileRoute("/methodology")({
  head: () => ({
    meta: [
      { title: "Methodology — UK Deal Pulse" },
      {
        name: "description",
        content:
          "How UK Deal Pulse discovers, sources, extracts and validates UK public takeover data, including coverage limits and disclaimer.",
      },
      { property: "og:title", content: "Methodology — UK Deal Pulse" },
      {
        property: "og:description",
        content: "Coverage, sources, AI-assisted extraction, validation, limitations and disclaimer.",
      },
      { property: "og:type", content: "article" },
      { name: "twitter:card", content: "summary" },
    ],
  }),
  component: MethodologyPage,
});

function MethodologyPage() {
  return (
    <div className="mx-auto max-w-[780px] px-4 py-8 sm:px-6">
      <PageHeader
        title="Methodology"
        description="How transactions are identified, structured and checked before they appear in the dataset."
      />

      <p className="mt-6 border-l-2 border-accent pl-4 text-[0.95rem] leading-relaxed">
        UK Deal Pulse tracks selected UK public takeover activity. Records are built from public
        primary-source announcements. Information that is not supported by a source is left
        undisclosed rather than estimated.
      </p>

      <Section title="Coverage">
        <p>
          Coverage focuses on takeovers of UK-listed companies, including recommended and hostile
          offers, schemes of arrangement and contractual offers. Private company deals, minority
          stake purchases and smaller transactions are generally out of scope. The dataset is
          selective and may be incomplete: the absence of a transaction does not mean it did not
          occur.
        </p>
      </Section>

      <Section title="Monitoring and discovery">
        <ul>
          <li>
            Current offer situations are monitored using publicly available Takeover Panel
            information.
          </li>
          <li>Regulatory announcements are monitored through RNS.</li>
          <li>
            An automated pipeline assists with discovering new transactions and processing the
            underlying announcements.
          </li>
        </ul>
      </Section>

      <Section title="Extraction and validation">
        <p>
          AI is used to extract structured transaction fields — deal value, offer price, premium,
          consideration structure, advisers and financing — from source documents. Extraction is a
          drafting aid, not the published record.
        </p>
        <ul>
          <li>Validation and duplicate checks are applied before publication.</li>
          <li>Each published field must be traceable to a cited source.</li>
          <li>
            Unsupported information remains &ldquo;Not disclosed&rdquo; and is never estimated or
            inferred.
          </li>
        </ul>
      </Section>

      <Section title="Limitations">
        <ul>
          <li>Announced values reflect figures at announcement and are not restated later.</li>
          <li>
            Premiums depend on the reference price used in each announcement, which varies between
            transactions.
          </li>
          <li>
            Adviser tables count appearances within this dataset only and are not official league
            tables.
          </li>
          <li>Transaction status can change after publication.</li>
          <li>The dataset may be incomplete.</li>
        </ul>
      </Section>

      <Section title="Disclaimer">
        <p>
          UK Deal Pulse is an informational and educational resource. It is not investment advice,
          and nothing here is a recommendation to buy or sell any security. Figures may contain
          errors or omissions; always consult the original public documents before relying on any
          number shown here.
        </p>
      </Section>

      <p className="mt-8 text-[0.7rem] text-muted-foreground/80">
        UK Deal Pulse was built and is maintained by Yash Nagpal.
      </p>
    </div>
  );
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <section className="mt-7 border-t border-border pt-5">
      <h2 className="text-base font-semibold tracking-tight">{title}</h2>
      <div className="mt-2.5 space-y-3 text-sm leading-relaxed text-muted-foreground [&_li]:mt-1.5 [&_ul]:list-disc [&_ul]:pl-5">
        {children}
      </div>
    </section>
  );
}
