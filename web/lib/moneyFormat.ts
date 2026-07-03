// Formatting helpers scoped to the dashboard screen. EUR is the primary,
// whole-euro display currency here; USD only ever appears as a quiet
// secondary ("≈ $…"), never a co-equal value. Percent/EUR deltas always
// carry an explicit sign so colour is never the only signal of direction.

// en-US (not en-IE) so USD renders as a plain "$" — en-IE's CLDR data
// disambiguates with "US$" since EUR is the region's home currency.
const eurWhole = new Intl.NumberFormat("en-US", {
  style: "currency",
  currency: "EUR",
  maximumFractionDigits: 0,
});

const usdWhole = new Intl.NumberFormat("en-US", {
  style: "currency",
  currency: "USD",
  maximumFractionDigits: 0,
});

export function formatEurWhole(value: number): string {
  return eurWhole.format(value);
}

export function formatUsdApprox(value: number): string {
  return `≈ ${usdWhole.format(value)}`;
}

export function formatSignedEurWhole(value: number): string {
  const sign = value > 0 ? "+" : value < 0 ? "-" : "";
  return `${sign}${eurWhole.format(Math.abs(value))}`;
}

export function formatSignedPct(value: number, digits = 1): string {
  if (value === 0) return `${(0).toFixed(digits)}%`;
  const sign = value > 0 ? "+" : "-";
  return `${sign}${Math.abs(value).toFixed(digits)}%`;
}

export function formatWeightPct(value: number): string {
  return `${Math.round(value)}%`;
}
