export const metadata = {
  title: "Impressum — Sunday",
};

export default function ImpressumPage() {
  return (
    <div className="space-y-6 fade-up">
      <header className="space-y-3">
        <p className="label">Legal</p>
        <h1 className="font-sans text-3xl font-semibold tracking-tight text-ink sm:text-4xl">
          Impressum
        </h1>
      </header>
      <p className="max-w-prose text-base leading-relaxed text-ink-muted">
        Our Impressum (provider identification under DDG §5) is being finalised with counsel and
        will appear here before public launch, with the operating entity, registration details,
        and contact address.
      </p>
    </div>
  );
}
