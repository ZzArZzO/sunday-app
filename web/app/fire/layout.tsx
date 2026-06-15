import type { Metadata } from "next";
import type { ReactNode } from "react";

// Page metadata lives here (a server component) so the page itself can be a
// client component for the static/Capacitor build.
export const metadata: Metadata = {
  title: "FIRE planner — Sunday",
  description: "Financial independence projection for your portfolio.",
};

export default function FireLayout({ children }: { children: ReactNode }) {
  return children;
}
