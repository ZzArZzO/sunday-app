import type { Config } from "tailwindcss";

/**
 * Modern design system — Linear / Vercel / Stripe-class.
 *
 * Light + dark mode via class strategy. Tokens are CSS variables defined in
 * globals.css so a single class swap (`dark`) re-themes the whole app.
 * Fonts (Geist Sans + Geist Mono) loaded via next/font in app/layout.tsx.
 */
const config: Config = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}"],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        bg: "rgb(var(--bg) / <alpha-value>)",
        surface: "rgb(var(--surface) / <alpha-value>)",
        "surface-2": "rgb(var(--surface-2) / <alpha-value>)",
        ink: {
          DEFAULT: "rgb(var(--ink) / <alpha-value>)",
          muted: "rgb(var(--ink-muted) / <alpha-value>)",
          subtle: "rgb(var(--ink-subtle) / <alpha-value>)",
        },
        rule: "rgb(var(--rule) / <alpha-value>)",
        accent: {
          DEFAULT: "rgb(var(--accent) / <alpha-value>)",
          fg: "rgb(var(--accent-fg) / <alpha-value>)",
          subtle: "rgb(var(--accent-subtle) / <alpha-value>)",
        },
        positive: {
          DEFAULT: "rgb(var(--positive) / <alpha-value>)",
          subtle: "rgb(var(--positive-subtle) / <alpha-value>)",
        },
        negative: {
          DEFAULT: "rgb(var(--negative) / <alpha-value>)",
          subtle: "rgb(var(--negative-subtle) / <alpha-value>)",
        },
        warn: {
          DEFAULT: "rgb(var(--warn) / <alpha-value>)",
          subtle: "rgb(var(--warn-subtle) / <alpha-value>)",
        },
      },
      fontFamily: {
        sans: ["var(--font-geist-sans)", "ui-sans-serif", "system-ui", "sans-serif"],
        mono: ["var(--font-geist-mono)", "ui-monospace", "monospace"],
      },
      letterSpacing: {
        tight: "-0.015em",
        tighter: "-0.025em",
        label: "0.06em",
      },
      borderRadius: {
        sm: "0.375rem",
        DEFAULT: "0.5rem",
        md: "0.75rem",
        lg: "1rem",
        xl: "1.5rem",
        "2xl": "1.75rem",
      },
      boxShadow: {
        soft: "0 1px 2px rgb(var(--shadow) / 0.06), 0 4px 12px rgb(var(--shadow) / 0.04)",
        elev:
          "0 1px 2px rgb(var(--shadow) / 0.08), 0 8px 24px rgb(var(--shadow) / 0.06), 0 24px 48px rgb(var(--shadow) / 0.04)",
      },
      maxWidth: {
        prose: "62ch",
        column: "44rem",
      },
      transitionTimingFunction: {
        out: "cubic-bezier(0.22, 1, 0.36, 1)",
      },
    },
  },
  plugins: [],
};

export default config;
