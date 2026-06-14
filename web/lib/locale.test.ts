import { describe, expect, it } from "vitest";

import { DEFAULT_LOCALE, localeForCountry } from "./locale";

describe("localeForCountry", () => {
  it("defaults to the DE-first beachhead", () => {
    expect(DEFAULT_LOCALE).toBe("de-DE");
  });

  it("maps DE and AT to de-DE", () => {
    expect(localeForCountry("DE")).toBe("de-DE");
    expect(localeForCountry("AT")).toBe("de-DE");
  });

  it("maps PT to pt-PT", () => {
    expect(localeForCountry("PT")).toBe("pt-PT");
  });

  it("is case-insensitive", () => {
    expect(localeForCountry("de")).toBe("de-DE");
    expect(localeForCountry("pt")).toBe("pt-PT");
  });

  it("falls back to neutral en-IE for other countries", () => {
    expect(localeForCountry("FR")).toBe("en-IE");
    expect(localeForCountry("ES")).toBe("en-IE");
  });

  it("falls back to the default when country is missing", () => {
    expect(localeForCountry(null)).toBe(DEFAULT_LOCALE);
    expect(localeForCountry(undefined)).toBe(DEFAULT_LOCALE);
  });
});
