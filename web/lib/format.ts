import type { DualMoney } from "@/lib/types";
import { DEFAULT_LOCALE, type SupportedLocale } from "@/lib/locale";

// Locale-aware money/percent/quantity formatting. Defaults to the DE-first
// beachhead (`1.234,56 €`); pass a locale (resolved from the user's country)
// to override. Formatters are cached per locale — they're relatively expensive
// to construct.

type Formatters = {
  eur: Intl.NumberFormat;
  usd: Intl.NumberFormat;
  pct: Intl.NumberFormat;
  qtyStock: Intl.NumberFormat;
  qtyCrypto: Intl.NumberFormat;
};

const CACHE = new Map<SupportedLocale, Formatters>();

function formatters(locale: SupportedLocale): Formatters {
  const cached = CACHE.get(locale);
  if (cached) return cached;
  const built: Formatters = {
    eur: new Intl.NumberFormat(locale, { style: "currency", currency: "EUR", maximumFractionDigits: 2 }),
    usd: new Intl.NumberFormat(locale, { style: "currency", currency: "USD", maximumFractionDigits: 2 }),
    pct: new Intl.NumberFormat(locale, { style: "percent", minimumFractionDigits: 2, maximumFractionDigits: 2 }),
    qtyStock: new Intl.NumberFormat(locale, { minimumFractionDigits: 0, maximumFractionDigits: 4 }),
    qtyCrypto: new Intl.NumberFormat(locale, { minimumFractionDigits: 0, maximumFractionDigits: 8 }),
  };
  CACHE.set(locale, built);
  return built;
}

/** Dual-currency formatter — the project's canonical money display. EUR primary, USD reference. */
export function formatDual(money: DualMoney, locale: SupportedLocale = DEFAULT_LOCALE): string {
  const f = formatters(locale);
  return `${f.eur.format(Number(money.eur))} / ${f.usd.format(Number(money.usd))}`;
}

export function formatEur(value: string | number, locale: SupportedLocale = DEFAULT_LOCALE): string {
  return formatters(locale).eur.format(Number(value));
}

export function formatUsd(value: string | number, locale: SupportedLocale = DEFAULT_LOCALE): string {
  return formatters(locale).usd.format(Number(value));
}

export function formatPct(value: string | number, locale: SupportedLocale = DEFAULT_LOCALE): string {
  return formatters(locale).pct.format(Number(value) / 100);
}

/** Quantity formatter with the project's precision: 8 dp crypto, 4 dp stocks. */
export function formatQuantity(
  value: string | number,
  assetClass: string,
  locale: SupportedLocale = DEFAULT_LOCALE,
): string {
  const f = formatters(locale);
  return (assetClass === "crypto" ? f.qtyCrypto : f.qtyStock).format(Number(value));
}

/**
 * Date/time formatter. Deliberately locale-neutral (en-IE → "14 Jun 2026")
 * while the UI copy is English; full date localisation lands with i18n.
 */
export function formatDateTime(iso: string): string {
  return new Date(iso).toLocaleString("en-IE", {
    dateStyle: "medium",
    timeStyle: "short",
  });
}
