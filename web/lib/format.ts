import type { DualMoney } from "@/lib/types";

const EUR = new Intl.NumberFormat("en-IE", {
  style: "currency",
  currency: "EUR",
  maximumFractionDigits: 2,
});

const USD = new Intl.NumberFormat("en-US", {
  style: "currency",
  currency: "USD",
  maximumFractionDigits: 2,
});

const PCT = new Intl.NumberFormat("en-IE", {
  style: "percent",
  minimumFractionDigits: 2,
  maximumFractionDigits: 2,
});

/** Dual-currency formatter — the project's canonical money display. */
export function formatDual(money: DualMoney): string {
  return `${EUR.format(Number(money.eur))} / ${USD.format(Number(money.usd))}`;
}

export function formatEur(value: string | number): string {
  return EUR.format(Number(value));
}

export function formatUsd(value: string | number): string {
  return USD.format(Number(value));
}

export function formatPct(value: string | number): string {
  return PCT.format(Number(value) / 100);
}

/** Quantity formatter with the project's precision: 8 dp crypto, 4 dp stocks. */
export function formatQuantity(value: string | number, assetClass: string): string {
  const dp = assetClass === "crypto" ? 8 : 4;
  return new Intl.NumberFormat("en-IE", {
    minimumFractionDigits: 0,
    maximumFractionDigits: dp,
  }).format(Number(value));
}

export function formatDateTime(iso: string): string {
  return new Date(iso).toLocaleString("en-IE", {
    dateStyle: "medium",
    timeStyle: "short",
  });
}
