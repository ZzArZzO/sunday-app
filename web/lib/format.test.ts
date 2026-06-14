import { describe, expect, it } from "vitest";

import { formatDual, formatEur, formatPct, formatQuantity } from "./format";

// Non-breaking spaces appear in some locale outputs (e.g. before the € / % in
// de-DE). Normalise them so assertions are robust across ICU versions.
const norm = (s: string) => s.replace(/ /g, " ");

describe("formatEur", () => {
  it("formats German numbers with dot-thousands and comma-decimal", () => {
    expect(norm(formatEur(1234.56, "de-DE"))).toBe("1.234,56 €");
  });

  it("formats neutral en-IE with comma-thousands and dot-decimal", () => {
    expect(norm(formatEur(1234.56, "en-IE"))).toBe("€1,234.56");
  });

  it("uses a comma decimal separator for pt-PT", () => {
    // pt-PT grouping is ICU-dependent; assert the comma decimal structurally.
    expect(norm(formatEur(1234.56, "pt-PT"))).toContain(",56");
  });

  it("defaults to de-DE when no locale is given", () => {
    expect(norm(formatEur(1234.56))).toBe("1.234,56 €");
  });

  it("accepts string input", () => {
    expect(norm(formatEur("1000", "de-DE"))).toBe("1.000,00 €");
  });
});

describe("formatPct", () => {
  it("divides by 100 and formats per locale", () => {
    expect(norm(formatPct(31.5, "de-DE"))).toBe("31,50 %");
    expect(norm(formatPct(31.5, "en-IE"))).toBe("31.50%");
  });
});

describe("formatDual", () => {
  it("shows EUR primary and USD reference", () => {
    const out = norm(formatDual({ eur: "1000", usd: "1080" }, "de-DE"));
    expect(out).toContain("1.000,00 €");
    expect(out).toContain("/");
    expect(out).toContain("$");
  });
});

describe("formatQuantity", () => {
  it("uses 8 dp for crypto and up to 4 dp for stocks", () => {
    expect(norm(formatQuantity("0.12345678", "crypto", "en-IE"))).toBe("0.12345678");
    expect(norm(formatQuantity("12.5", "stock", "en-IE"))).toBe("12.5");
  });
});
