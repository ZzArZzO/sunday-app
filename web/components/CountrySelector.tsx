"use client";

import { useEffect, useState } from "react";

import { fetchSupportedCountries, updateCountry } from "@/lib/api";
import type { SupportedCountry } from "@/lib/types";

interface CountrySelectorProps {
  /** The currently-applied country code (from the tax summary). */
  current: string;
  /** Called after a successful change so the caller can refetch country-dependent data. */
  onChanged: () => void;
}

/**
 * Tax-residence picker. Drives the tax summary and locale formatting. Lists only
 * countries the tax engine supports (the eurozone), fetched from the API so it
 * never drifts from the backend profiles.
 */
export function CountrySelector({ current, onChanged }: CountrySelectorProps) {
  const [countries, setCountries] = useState<SupportedCountry[]>([]);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    fetchSupportedCountries()
      .then((list) => {
        if (active) setCountries(list);
      })
      .catch(() => {
        /* selector stays hidden if the list can't load */
      });
    return () => {
      active = false;
    };
  }, []);

  async function onSelect(code: string) {
    if (code === current) return;
    setSaving(true);
    setError(null);
    try {
      await updateCountry(code);
      onChanged();
    } catch {
      setError("Couldn't update");
    } finally {
      setSaving(false);
    }
  }

  if (countries.length === 0) return null;

  return (
    <label className="flex items-center gap-1.5 text-xs text-ink-subtle">
      <span className="sr-only">Tax residence</span>
      <select
        value={current}
        disabled={saving}
        onChange={(e) => onSelect(e.target.value)}
        className="rounded-md border border-rule bg-surface-2 px-2 py-1 text-xs text-ink disabled:opacity-50"
        aria-label="Tax-residence country"
      >
        {countries.map((c) => (
          <option key={c.code} value={c.code}>
            {c.name}
          </option>
        ))}
      </select>
      {error ? <span className="text-negative">{error}</span> : null}
    </label>
  );
}
