import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: {
          DEFAULT: "#0f172a",
          muted: "#475569",
          subtle: "#94a3b8",
        },
        paper: {
          DEFAULT: "#fafaf7",
          card: "#ffffff",
        },
        accent: {
          DEFAULT: "#3b82f6",
          subtle: "#dbeafe",
        },
        positive: "#15803d",
        negative: "#b91c1c",
      },
      fontFamily: {
        sans: ["ui-sans-serif", "system-ui", "-apple-system", "Segoe UI", "Roboto", "sans-serif"],
        mono: ["ui-monospace", "SFMono-Regular", "Menlo", "monospace"],
      },
    },
  },
  plugins: [],
};

export default config;
