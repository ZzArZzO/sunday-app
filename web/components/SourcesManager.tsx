"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import {
  connectAddress,
  connectExchange,
  disconnectConnection,
  fetchConnections,
  fetchSubscription,
  syncConnection,
} from "@/lib/api";
import { BROKERS } from "@/lib/brokers";
import type { Connection, Subscription } from "@/lib/types";

const KIND_LABEL: Record<Connection["kind"], string> = {
  manual: "Manual entry",
  csv: "CSV import",
  address: "Wallet address",
  exchange: "Exchange",
};

// Bitvavo first — the EUR-native EU leader this app is built around; Kraken,
// Coinbase and Binance round out what EU retail actually uses. Mirrors
// SUPPORTED_EXCHANGES in api/app/services/connectors/exchange.py.
const EXCHANGES = ["bitvavo", "kraken", "coinbase", "binance"];

const EXCHANGE_LABEL: Record<string, string> = {
  bitvavo: "Bitvavo",
  kraken: "Kraken",
  coinbase: "Coinbase",
  binance: "Binance",
};

function errorMessage(err: unknown): string {
  if (!(err instanceof Error)) return String(err);
  // http() throws "API <status> <path>: <detail>"; surface just the detail when present.
  const m = err.message.match(/:\s*(\{.*\}|.+)$/);
  if (m) {
    try {
      const parsed = JSON.parse(m[1]) as { detail?: string };
      if (parsed.detail) return parsed.detail;
    } catch {
      return m[1];
    }
  }
  return err.message;
}

export function SourcesManager() {
  const [connections, setConnections] = useState<Connection[]>([]);
  const [sub, setSub] = useState<Subscription | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [busyId, setBusyId] = useState<number | null>(null);

  async function refresh() {
    const { connections } = await fetchConnections();
    setConnections(connections);
  }

  useEffect(() => {
    (async () => {
      try {
        const [list, subscription] = await Promise.all([fetchConnections(), fetchSubscription()]);
        setConnections(list.connections);
        setSub(subscription);
      } catch (err) {
        setError(errorMessage(err));
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  async function onSync(id: number) {
    setBusyId(id);
    setNotice(null);
    setError(null);
    try {
      const result = await syncConnection(id);
      setNotice(`Synced — ${result.positions_synced} holding(s) updated.`);
      await refresh();
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setBusyId(null);
    }
  }

  async function onDisconnect(id: number) {
    setBusyId(id);
    setNotice(null);
    setError(null);
    try {
      await disconnectConnection(id);
      setNotice("Source disconnected and its holdings removed.");
      await refresh();
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setBusyId(null);
    }
  }

  if (loading) {
    return <p className="card p-6 text-sm text-ink-muted">Loading your sources…</p>;
  }

  const isPro = sub?.is_pro ?? false;

  return (
    <div className="space-y-10">
      {notice ? (
        <div role="status" className="rounded-md border border-positive/30 bg-positive-subtle/40 p-3 text-sm text-ink">
          {notice}
        </div>
      ) : null}
      {error ? (
        <div role="alert" className="rounded-md border border-negative/30 bg-negative-subtle/40 p-3 text-sm">
          <span className="font-medium text-negative">Something went wrong. </span>
          <span className="text-ink">{error}</span>
        </div>
      ) : null}

      <section className="space-y-3">
        <p className="label">Connected sources</p>
        {connections.length === 0 ? (
          <p className="card p-5 text-sm text-ink-muted">
            No sources yet. Add one below — import a broker CSV, or connect a wallet or exchange.
          </p>
        ) : (
          <ul className="space-y-2">
            {connections.map((c) => (
              <ConnectionRow
                key={c.id}
                connection={c}
                busy={busyId === c.id}
                onSync={() => onSync(c.id)}
                onDisconnect={() => onDisconnect(c.id)}
              />
            ))}
          </ul>
        )}
      </section>

      <section className="space-y-4">
        <p className="label">Add a source</p>
        <div className="grid gap-4 lg:grid-cols-3">
          <article className="card flex flex-col gap-2 p-5">
            <p className="font-medium text-ink">Broker CSV</p>
            <p className="text-sm text-ink-muted">Stocks, ETFs and crypto — no broker login required.</p>
            <ul className="flex flex-1 flex-wrap gap-1.5">
              {BROKERS.filter((b) => b.id !== "other").map((b) => (
                <li
                  key={b.id}
                  className="rounded-full border border-rule bg-surface-2 px-2 py-0.5 text-xs text-ink-muted"
                >
                  {b.name}
                </li>
              ))}
            </ul>
            <Link href="/upload" className="btn btn-primary mt-2 self-start">
              Import a CSV
            </Link>
          </article>

          <WalletForm
            isPro={isPro}
            onDone={(msg) => {
              setNotice(msg);
              void refresh();
            }}
            onError={setError}
          />

          <ExchangeForm
            isPro={isPro}
            onDone={(msg) => {
              setNotice(msg);
              void refresh();
            }}
            onError={setError}
          />
        </div>
        <p className="text-xs text-ink-subtle">
          None of these need your broker login. Wallet and exchange sync are read-only — we read public
          balances, never private keys, and can&apos;t move funds.
        </p>
      </section>
    </div>
  );
}

function ConnectionRow({
  connection,
  busy,
  onSync,
  onDisconnect,
}: {
  connection: Connection;
  busy: boolean;
  onSync: () => void;
  onDisconnect: () => void;
}) {
  const live = connection.kind === "address" || connection.kind === "exchange";
  return (
    <li className="card flex flex-wrap items-center justify-between gap-3 p-4">
      <div className="min-w-0">
        <p className="flex items-center gap-2">
          <span className="font-medium text-ink">{connection.label}</span>
          <StatusBadge status={connection.status} />
        </p>
        <p className="mt-0.5 text-xs text-ink-subtle">
          {KIND_LABEL[connection.kind]}
          {connection.last_synced_at
            ? ` · synced ${new Date(connection.last_synced_at).toLocaleString()}`
            : null}
        </p>
        {connection.status === "error" && connection.error_detail ? (
          <p className="mt-1 text-xs text-negative">{connection.error_detail}</p>
        ) : null}
      </div>
      <div className="flex flex-none gap-2">
        {live ? (
          <button type="button" onClick={onSync} disabled={busy} className="btn btn-ghost">
            {busy ? "Syncing…" : "Re-sync"}
          </button>
        ) : null}
        <button
          type="button"
          onClick={onDisconnect}
          disabled={busy}
          className="btn btn-ghost text-negative"
        >
          Disconnect
        </button>
      </div>
    </li>
  );
}

function StatusBadge({ status }: { status: Connection["status"] }) {
  const styles: Record<Connection["status"], string> = {
    active: "bg-positive-subtle text-positive",
    error: "bg-negative-subtle text-negative",
    disconnected: "bg-surface-2 text-ink-muted",
  };
  return (
    <span className={`rounded-full px-2 py-0.5 text-xs font-medium ${styles[status]}`}>{status}</span>
  );
}

function ProGate() {
  return (
    <div className="mt-2 rounded-md border border-rule bg-surface-2/50 p-3 text-sm text-ink-muted">
      Live sync is a Pro feature.{" "}
      <Link href="/billing" className="font-medium text-accent hover:underline">
        Upgrade to connect →
      </Link>
    </div>
  );
}

function WalletForm({
  isPro,
  onDone,
  onError,
}: {
  isPro: boolean;
  onDone: (msg: string) => void;
  onError: (msg: string) => void;
}) {
  const [address, setAddress] = useState("");
  const [busy, setBusy] = useState(false);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    onError("");
    try {
      const result = await connectAddress(address.trim());
      onDone(`Wallet connected — ${result.positions_synced} holding(s) synced.`);
      setAddress("");
    } catch (err) {
      onError(errorMessage(err));
    } finally {
      setBusy(false);
    }
  }

  return (
    <article className="card flex flex-col gap-2 p-5">
      <p className="font-medium text-ink">Crypto wallet</p>
      <p className="text-sm text-ink-muted">
        Paste a public address on Ethereum, its L2s, or Solana — read-only, no keys.
      </p>
      {isPro ? (
        <form onSubmit={submit} className="mt-2 space-y-2">
          <input
            type="text"
            value={address}
            onChange={(e) => setAddress(e.target.value)}
            placeholder="0x… or a Solana address"
            spellCheck={false}
            className="w-full rounded-md border border-rule bg-surface px-3 py-2 font-mono text-sm text-ink"
          />
          <button type="submit" disabled={busy || !address.trim()} className="btn btn-primary w-full">
            {busy ? "Connecting…" : "Connect wallet"}
          </button>
        </form>
      ) : (
        <ProGate />
      )}
    </article>
  );
}

function ExchangeForm({
  isPro,
  onDone,
  onError,
}: {
  isPro: boolean;
  onDone: (msg: string) => void;
  onError: (msg: string) => void;
}) {
  const [exchange, setExchange] = useState(EXCHANGES[0]);
  const [apiKey, setApiKey] = useState("");
  const [apiSecret, setApiSecret] = useState("");
  const [busy, setBusy] = useState(false);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    onError("");
    try {
      const result = await connectExchange(exchange, apiKey.trim(), apiSecret.trim());
      onDone(`${exchange} connected — ${result.positions_synced} holding(s) synced.`);
      setApiKey("");
      setApiSecret("");
    } catch (err) {
      onError(errorMessage(err));
    } finally {
      setBusy(false);
    }
  }

  return (
    <article className="card flex flex-col gap-2 p-5">
      <p className="font-medium text-ink">Exchange</p>
      <p className="text-sm text-ink-muted">A read-only API key — no trading, no withdrawals.</p>
      {isPro ? (
        <form onSubmit={submit} className="mt-2 space-y-2">
          <select
            value={exchange}
            onChange={(e) => setExchange(e.target.value)}
            className="w-full rounded-md border border-rule bg-surface px-3 py-2 text-sm text-ink"
          >
            {EXCHANGES.map((x) => (
              <option key={x} value={x}>
                {EXCHANGE_LABEL[x] ?? x}
              </option>
            ))}
          </select>
          <input
            type="text"
            value={apiKey}
            onChange={(e) => setApiKey(e.target.value)}
            placeholder="API key"
            spellCheck={false}
            className="w-full rounded-md border border-rule bg-surface px-3 py-2 font-mono text-sm text-ink"
          />
          <input
            type="password"
            value={apiSecret}
            onChange={(e) => setApiSecret(e.target.value)}
            placeholder="API secret"
            className="w-full rounded-md border border-rule bg-surface px-3 py-2 font-mono text-sm text-ink"
          />
          <button
            type="submit"
            disabled={busy || !apiKey.trim() || !apiSecret.trim()}
            className="btn btn-primary w-full"
          >
            {busy ? "Connecting…" : "Connect exchange"}
          </button>
        </form>
      ) : (
        <ProGate />
      )}
    </article>
  );
}
