"use client";

import { BROKERS, type Broker } from "@/lib/brokers";

// First step of the import wizard: "Where do you invest?" Picking a broker
// reveals its 2-step export guide before the drag-drop, turning "figure it out
// yourself" into "follow these steps".
export function BrokerPicker({ onSelect }: { onSelect: (broker: Broker) => void }) {
  return (
    <div className="space-y-4">
      <p className="label">Where do you invest?</p>
      <div className="grid gap-3 sm:grid-cols-2">
        {BROKERS.map((broker) => (
          <button
            key={broker.id}
            type="button"
            onClick={() => onSelect(broker)}
            className="card group flex flex-col items-start gap-1 p-5 text-left transition-colors hover:border-accent"
          >
            <span className="flex items-center gap-2">
              <span className="font-medium text-ink">{broker.name}</span>
              {broker.primary ? (
                <span className="rounded-full bg-accent-subtle px-2 py-0.5 text-xs font-medium text-accent">
                  Popular
                </span>
              ) : null}
            </span>
            <span className="text-sm text-ink-muted">{broker.blurb}</span>
          </button>
        ))}
      </div>
    </div>
  );
}
