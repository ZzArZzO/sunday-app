import type { Metadata, Viewport } from "next";
import type { ReactNode } from "react";
import { GeistMono } from "geist/font/mono";
import { GeistSans } from "geist/font/sans";

import "./globals.css";
import { BiometricGate } from "@/components/BiometricGate";
import { MobileTabBar } from "@/components/MobileTabBar";
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
        <BiometricGate>
          <NavBar />
          <main className="container-narrow pt-8 pb-24 sm:pt-12 md:pt-16 md:pb-16">{children}</main>
          <MobileTabBar />
          <footer className="container-narrow border-t border-rule py-8 pb-24 text-xs text-ink-subtle md:pb-8">
            <p>
              Sunday is information, not advice. Numbers are computed deterministically; the
              narrative sections are generated with AI assistance.
            </p>
            <nav className="mt-3 flex gap-4">
              <a href="/terms" className="hover:underline">
                Terms
              </a>
              <a href="/privacy" className="hover:underline">
                Privacy
              </a>
              <a href="/impressum" className="hover:underline">
                Impressum
              </a>
            </nav>
          </footer>
        </BiometricGate>
      </body>
    </html>
  );
}
