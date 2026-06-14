// Locale resolution for number/currency/percent formatting.
//
// The beachhead is DE → PT, so the app default is German formatting
// (`1.234,56 €`). Country is resolved to a BCP-47 locale; unknown countries
// fall back to a neutral EU-English locale. This is *number* formatting only —
// UI-string localisation (i18n) is a separate, later phase.

export type SupportedLocale = "de-DE" | "pt-PT" | "en-IE";

/** App default — the DE-first beachhead. */
export const DEFAULT_LOCALE: SupportedLocale = "de-DE";

const COUNTRY_TO_LOCALE: Record<string, SupportedLocale> = {
  DE: "de-DE",
  AT: "de-DE",
  PT: "pt-PT",
};

/**
 * Map an ISO country code (e.g. from the user's tax residence) to the locale
 * used for formatting. Defaults to DE; unknown countries get neutral en-IE.
 */
export function localeForCountry(country?: string | null): SupportedLocale {
  if (!country) return DEFAULT_LOCALE;
  return COUNTRY_TO_LOCALE[country.toUpperCase()] ?? "en-IE";
}
