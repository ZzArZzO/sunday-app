export const metadata = {
  title: "Terms of Service — Sunday",
};

export default function TermsPage() {
  return (
    <div className="space-y-6 fade-up">
      <header className="space-y-3">
        <p className="label">Legal</p>
        <h1 className="font-sans text-3xl font-semibold tracking-tight text-ink sm:text-4xl">
          Terms of Service
        </h1>
      </header>
      <p className="max-w-prose text-base leading-relaxed text-ink-muted">
        Our full terms of service are being finalised with counsel and will appear here before
        public launch. Sunday provides information only and is not investment advice.
      </p>
    </div>
  );
}
