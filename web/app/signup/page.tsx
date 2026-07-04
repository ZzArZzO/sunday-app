import Link from "next/link";

import { MagicLinkForm } from "@/components/MagicLinkForm";

export const metadata = {
  title: "Sign up — Sunday",
};

export default function SignUpPage() {
  return (
    <div className="container-prose mx-auto max-w-md space-y-8 py-10">
      <header className="space-y-2">
        <p className="label">Sign up</p>
        <h1 className="font-sans text-3xl font-semibold tracking-tight text-ink">
          Create your account
        </h1>
        <p className="text-base leading-relaxed text-ink-muted">
          No password to create, nothing to remember. Enter your email, we&apos;ll send a one-tap
          link, and you&apos;re in — import a portfolio and see your first briefing in minutes.
        </p>
      </header>

      <MagicLinkForm submitLabel="Create account" sentHeading="Almost there — check your inbox" />

      <p className="text-sm text-ink-muted">
        Already have an account?{" "}
        <Link href="/signin" className="font-medium text-accent hover:underline">
          Log in
        </Link>
      </p>

      <p className="text-xs leading-relaxed text-ink-subtle">
        Information and education only — Sunday is not a financial adviser. No broker login; your
        data stays yours.
      </p>
    </div>
  );
}
