import type { Metadata, Viewport } from "next";
import type { ReactNode } from "react";
import { GeistMono } from "geist/font/mono";
import { GeistSans } from "geist/font/sans";

import "./globals.css";
import { NavBar } from "@/components/NavBar";

export const metadata: Metadata = {
  title: "Sunday — a portfolio briefing for the rest of the week",
  description:
    "A weekly portfolio briefing for self-directed EU retail investors. Not investment advice.",
  applicationName: "Sunday",
  appleWebApp: {
    capable: true,
    statusBarStyle: "default",
    title: "Sunday",
  },
  formatDetection: {
    telephone: false,
  },
};

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  viewportFit: "cover",
  themeColor: [
    { media: "(prefers-color-scheme: light)", color: "#fafaf9" },
    { media: "(prefers-color-scheme: dark)", color: "#09090b" },
  ],
};

/**
 * Inline theme script: sets the `dark` class before first paint based on
 * persisted preference or `prefers-color-scheme`. Avoids a light→dark flash.
 */
const themeInitScript = `
(function() {
  try {
    var stored = localStorage.getItem('sunday-theme');
    var preferred = window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
    var theme = stored || preferred;
    if (theme === 'dark') document.documentElement.classList.add('dark');
  } catch (_) {}
})();
`;

export default function RootLayout({ children }: { children: ReactNode }) {
  const fontVars = `${GeistSans.variable} ${GeistMono.variable}`;
  return (
    <html lang="en" className={fontVars} suppressHydrationWarning>
      <head>
        <script dangerouslySetInnerHTML={{ __html: themeInitScript }} />
      </head>
      <body className="min-h-dvh">
        <NavBar />
        <main className="container-narrow py-8 sm:py-12 md:py-16">{children}</main>
        <footer className="container-narrow border-t border-rule py-8 text-xs text-ink-subtle">
          <p>
            Sunday is information, not advice. Numbers are computed deterministically; the narrative
            sections are generated with AI assistance.
          </p>
        </footer>
      </body>
    </html>
  );
}
