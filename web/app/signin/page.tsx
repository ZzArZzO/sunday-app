import Link from "next/link";

import { MagicLinkForm } from "@/components/MagicLinkForm";

export const metadata = {
  title: "Log in — Sunday",
};

export default function SignInPage() {
  return (
    <div className="container-prose mx-auto max-w-md space-y-8 py-10">
      <header className="space-y-2">
        <p className="label">Log in</p>
        <h1 className="font-sans text-3xl font-semibold tracking-tight text-ink">Welcome back</h1>
        <p className="text-base leading-relaxed text-ink-muted">
          Enter your email and we&apos;ll send you a one-tap link. No password to remember.
        </p>
      </header>

      <MagicLinkForm submitLabel="Send log-in link" sentHeading="Check your inbox" />

      <p className="text-sm text-ink-muted">
        New to Sunday?{" "}
        <Link href="/signup" className="font-medium text-accent hover:underline">
          Create an account
        </Link>
      </p>

      <p className="text-xs leading-relaxed text-ink-subtle">
        Information and education only — Sunday is not a financial adviser. No broker login; your
        data stays yours.
      </p>
    </div>
  );
}
