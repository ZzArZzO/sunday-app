"use client";

import { useState } from "react";

import { BrokerPicker } from "@/components/BrokerPicker";
import { CsvUploader } from "@/components/CsvUploader";
import type { Broker } from "@/lib/brokers";

// Orchestrates the import flow: pick broker → see its export guide → drag-drop
// (CsvUploader handles preview → confirm). The chosen broker labels the
// Connection the import creates, so it shows up in the user's sources.
export function ImportWizard() {
  const [broker, setBroker] = useState<Broker | null>(null);

  if (broker === null) {
    return <BrokerPicker onSelect={setBroker} />;
  }

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between gap-3">
        <p className="label">Importing from {broker.name}</p>
        <button
          type="button"
          onClick={() => setBroker(null)}
          className="text-sm font-medium text-accent hover:underline"
        >
          ← Change broker
        </button>
      </div>

      <ol className="card space-y-2 p-5 text-sm text-ink-muted">
        {broker.steps.map((step, i) => (
          <li key={step} className="flex gap-3">
            <span
              aria-hidden
              className="mt-0.5 inline-flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-surface-2 text-xs font-medium text-ink"
            >
              {i + 1}
            </span>
            <span className="text-ink">{step}</span>
          </li>
        ))}
        {broker.note ? <li className="pt-1 text-xs text-ink-subtle">{broker.note}</li> : null}
      </ol>

      <CsvUploader broker={broker.name} />
    </div>
  );
}
