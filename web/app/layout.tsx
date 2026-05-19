import type { Metadata } from "next";
import type { ReactNode } from "react";

import "./globals.css";
import { NavBar } from "@/components/NavBar";

export const metadata: Metadata = {
  title: "Sunday — portfolio briefings",
  description:
    "A Sunday-evening portfolio briefing for self-directed EU retail investors. Not investment advice.",
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body>
        <NavBar />
        <main className="container-narrow py-10">{children}</main>
      </body>
    </html>
  );
}
