"use client";

import { useState } from "react";

import { fetchBriefingPdf, sendMyBriefing } from "@/lib/api";

type PdfStatus =
  | { kind: "idle" }
  | { kind: "loading" }
  | { kind: "error"; message: string };

type EmailStatus =
  | { kind: "idle" }
  | { kind: "loading" }
  | { kind: "sent"; email: string; dryRun: boolean }
  | { kind: "error"; message: string };

function errorMessage(err: unknown): string {
  return err instanceof Error ? err.message : String(err);
}

/**
 * Sprint 3 delivery actions for the briefing: download the one-page PDF and
 * email this week's briefing to the signed-in user. Both hit endpoints that are
 * already live; email is dry-run (rendered + logged, not sent) without a Resend key.
 */
export function BriefingActions() {
  const [pdf, setPdf] = useState<PdfStatus>({ kind: "idle" });
  const [email, setEmail] = useState<EmailStatus>({ kind: "idle" });

  async function downloadPdf() {
    setPdf({ kind: "loading" });
    try {
      const blob = await fetchBriefingPdf();
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = "sunday-briefing.pdf";
      document.body.appendChild(a);
      a.click();
      a.remove();
      URL.revokeObjectURL(url);
      setPdf({ kind: "idle" });
    } catch (err) {
      setPdf({ kind: "error", message: errorMessage(err) });
    }
  }

  async function emailMe() {
    setEmail({ kind: "loading" });
    try {
      const res = await sendMyBriefing();
      if (!res.ok) {
        setEmail({ kind: "error", message: res.error ?? "Delivery failed" });
        return;
      }
      setEmail({ kind: "sent", email: res.email, dryRun: res.dry_run });
    } catch (err) {
      setEmail({ kind: "error", message: errorMessage(err) });
    }
  }

  return (
    <div className="flex flex-wrap items-center gap-3">
      <button
        type="button"
        onClick={downloadPdf}
        disabled={pdf.kind === "loading"}
        className="btn btn-ghost"
      >
        {pdf.kind === "loading" ? "Preparing…" : "Download PDF"}
      </button>
      <button
        type="button"
        onClick={emailMe}
        disabled={email.kind === "loading"}
        className="btn btn-ghost"
      >
        {email.kind === "loading" ? "Sending…" : "Email me this briefing"}
      </button>

      {email.kind === "sent" ? (
        <span className="text-sm text-ink-muted">
          {email.dryRun
            ? `Dry-run — rendered for ${email.email}, but no email provider is configured.`
            : `Sent to ${email.email}.`}
        </span>
      ) : null}
      {pdf.kind === "error" ? (
        <span className="text-sm text-negative" role="alert">
          {pdf.message}
        </span>
      ) : null}
      {email.kind === "error" ? (
        <span className="text-sm text-negative" role="alert">
          {email.message}
        </span>
      ) : null}
    </div>
  );
}
