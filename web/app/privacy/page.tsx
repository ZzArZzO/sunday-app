export const metadata = {
  title: "Privacy Policy — Sunday",
};

export default function PrivacyPage() {
  return (
    <div className="space-y-6 fade-up">
      <header className="space-y-3">
        <p className="label">Legal</p>
        <h1 className="font-sans text-3xl font-semibold tracking-tight text-ink sm:text-4xl">
          Privacy Policy
        </h1>
      </header>
      <p className="max-w-prose text-base leading-relaxed text-ink-muted">
        Our full GDPR privacy policy is being finalised with counsel and will appear here before
        public launch. It will cover what data we process, why, how long we keep it, and your
        rights as a data subject.
      </p>
    </div>
  );
}
