export const metadata = {
  title: "Privacy Policy — Sunday",
};

// DRAFT — written to unblock Stripe account activation, which requires a
// live, real (non-placeholder) privacy policy. Deliberately omits a business
// registration number (NIF) — founder's choice not to publish it; note this
// may leave a gap under EU e-Commerce Directive provider-transparency rules,
// separate from GDPR itself. This has NOT been reviewed by counsel — see
// docs/business/DEPLOYMENT_AND_MARKETING.md A.12 for the full pre-public-
// launch legal gate this is one part of.

export default function PrivacyPage() {
  return (
    <div className="space-y-10 fade-up">
      <header className="space-y-3">
        <p className="label">Legal</p>
        <h1 className="font-sans text-3xl font-semibold tracking-tight text-ink sm:text-4xl">
          Privacy Policy
        </h1>
        <p className="text-sm text-ink-subtle">Last updated: 4 July 2026 · Draft pending legal review</p>
      </header>

      <div className="max-w-prose space-y-8 text-base leading-relaxed text-ink-muted">
        <Section title="1. Who we are">
          <p>
            Sunday (&quot;Sunday&quot;, &quot;we&quot;, &quot;us&quot;) is operated by{" "}
            <strong className="text-ink">Afonso José Carvalho Marques da Costa</strong>, a sole
            trader (trabalhador independente) based in Portugal. We are the data controller for
            the personal data described in this policy.
          </p>
          <p>
            Contact for any privacy question or request:{" "}
            <strong className="text-ink">hi@sundayfolio.com</strong>.
          </p>
        </Section>

        <Section title="2. What data we process">
          <p>To provide the weekly briefing and the underlying dashboard, we process:</p>
          <ul className="list-disc space-y-1.5 pl-5">
            <li>
              <strong className="text-ink">Account data</strong> — your email address, and your
              country and timezone (used to route the tax engine and the weekly send time).
            </li>
            <li>
              <strong className="text-ink">Portfolio data</strong> — holdings, quantities, cost
              basis, and transaction history you provide via CSV upload, or via a wallet address /
              exchange API key you choose to connect. We never receive private keys, and exchange
              connections are read-only.
            </li>
            <li>
              <strong className="text-ink">Usage data</strong> — questions you ask the AI assistant,
              and which briefing sections you view, so we can generate and improve the product.
            </li>
            <li>
              <strong className="text-ink">Billing data</strong> — handled directly by Stripe; we
              store only your subscription status and Stripe customer reference, never your card
              details.
            </li>
            <li>
              <strong className="text-ink">Technical data</strong> — IP address and basic request
              logs, retained briefly for security and abuse prevention.
            </li>
          </ul>
        </Section>

        <Section title="3. Why we process it, and on what basis">
          <ul className="list-disc space-y-1.5 pl-5">
            <li>
              <strong className="text-ink">Performance of a contract</strong> — generating your
              dashboard and weekly briefing, running your subscription, and responding to support
              requests.
            </li>
            <li>
              <strong className="text-ink">Legitimate interest</strong> — securing your account
              (fraud/abuse prevention), and improving the product from aggregate, de-identified
              usage patterns.
            </li>
            <li>
              <strong className="text-ink">Consent</strong> — the optional weekly email delivery,
              which you opt into and can withdraw at any time from your account settings.
            </li>
          </ul>
        </Section>

        <Section title="4. Who we share it with">
          <p>
            We use the following processors to operate Sunday. Each is bound by a data processing
            agreement; none receive more data than they need to perform their function.
          </p>
          <ul className="list-disc space-y-1.5 pl-5">
            <li>
              <strong className="text-ink">Anthropic</strong> (EU region endpoint) — generates the
              AI narrative in your briefing and powers the chat assistant. Portfolio figures sent to
              the model are the minimum needed to answer your question; Anthropic does not use this
              data to train its models under our commercial agreement.
            </li>
            <li>
              <strong className="text-ink">Stripe</strong> — payment processing and subscription
              billing.
            </li>
            <li>
              <strong className="text-ink">Resend</strong> — delivery of the weekly briefing
              email.
            </li>
            <li>
              <strong className="text-ink">Supabase</strong> (Frankfurt, EU) — database hosting and
              authentication.
            </li>
            <li>
              <strong className="text-ink">Zerion</strong> — reads public wallet balances and
              transaction history for connected crypto addresses, if you choose to connect one.
            </li>
            <li>
              <strong className="text-ink">Market data providers</strong> (yfinance, Financial
              Modeling Prep, OpenFIGI) — used to fetch prices and resolve instrument identifiers;
              these receive tickers/ISINs, not your identity.
            </li>
          </ul>
          <p>
            We do not sell your data, and we do not share your portfolio contents with any
            advertising or analytics network.
          </p>
        </Section>

        <Section title="5. International transfers">
          <p>
            Where a processor is based outside the EEA, we rely on Standard Contractual Clauses or
            an equivalent adequacy mechanism to ensure your data receives the same level of
            protection as under GDPR.
          </p>
        </Section>

        <Section title="6. How long we keep it">
          <p>
            We retain account and portfolio data for as long as your account is active. If you
            delete your account, we erase your personal data within 30 days, except where we are
            legally required to retain billing records for tax purposes (typically 7–10 years,
            depending on jurisdiction).
          </p>
        </Section>

        <Section title="7. Your rights">
          <p>Under GDPR, you have the right to:</p>
          <ul className="list-disc space-y-1.5 pl-5">
            <li>Access the personal data we hold about you</li>
            <li>Correct inaccurate data</li>
            <li>Request erasure of your data (&quot;right to be forgotten&quot;)</li>
            <li>Export your data in a portable format</li>
            <li>Object to or restrict certain processing</li>
            <li>Withdraw consent at any time, where processing is based on consent</li>
            <li>
              Lodge a complaint with your local data protection supervisory authority, or with our
              lead authority, Portugal&apos;s Comissão Nacional de Proteção de Dados (CNPD)
            </li>
          </ul>
          <p>
            To exercise any of these rights, email{" "}
            <strong className="text-ink">hi@sundayfolio.com</strong>. We currently handle
            deletion and export requests manually and respond within 30 days; self-service tools are
            planned.
          </p>
        </Section>

        <Section title="8. Security">
          <p>
            Authentication is handled by Supabase Auth: passwords are stored hashed and salted,
            never in plain text, and an optional authenticator-app second factor (TOTP) is
            available from Account settings. Connected-exchange credentials are stored encrypted
            at rest. Traffic between your browser and our servers is encrypted in transit (TLS).
          </p>
        </Section>

        <Section title="9. Cookies">
          <p>
            We use a single essential session cookie to keep you signed in. We do not use
            advertising or third-party tracking cookies.
          </p>
        </Section>

        <Section title="10. Children">
          <p>Sunday is not directed at, and should not be used by, anyone under 18.</p>
        </Section>

        <Section title="11. Changes to this policy">
          <p>
            If we make material changes to this policy, we&apos;ll notify you by email before they
            take effect.
          </p>
        </Section>
      </div>
    </div>
  );
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <section className="space-y-3">
      <h2 className="font-sans text-xl font-semibold tracking-tight text-ink">{title}</h2>
      {children}
    </section>
  );
}
