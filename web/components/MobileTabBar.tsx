"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import type { ReactNode } from "react";

// Bottom tab bar for mobile (hidden on desktop and on the marketing landing
// page). Thumb-reachable, safe-area-padded, with 44px+ targets. Five primary
// destinations per the mobile UX research; the top NavBar rail is hidden below
// md so this is the single mobile nav.

type Tab = { href: string; label: string; icon: ReactNode };

const TABS: Tab[] = [
  { href: "/briefing", label: "Briefing", icon: <BriefingIcon /> },
  { href: "/dashboard", label: "Portfolio", icon: <DashboardIcon /> },
  { href: "/assistant", label: "Assistant", icon: <ChatIcon /> },
  { href: "/plan", label: "Plan", icon: <PlanIcon /> },
  { href: "/upload", label: "Import", icon: <ImportIcon /> },
];

function isActive(pathname: string, href: string): boolean {
  return pathname === href || pathname.startsWith(`${href}/`);
}

export function MobileTabBar() {
  const pathname = usePathname();
  // Keep the landing page clean — no app chrome there.
  if (pathname === "/") return null;

  return (
    <nav
      aria-label="Primary"
      className="fixed inset-x-0 bottom-0 z-40 border-t border-rule bg-bg/90 backdrop-blur-md md:hidden"
      style={{ paddingBottom: "env(safe-area-inset-bottom)" }}
    >
      <ul className="mx-auto flex max-w-5xl items-stretch">
        {TABS.map((tab) => {
          const active = isActive(pathname, tab.href);
          return (
            <li key={tab.href} className="flex-1">
              <Link
                href={tab.href}
                aria-current={active ? "page" : undefined}
                className={`flex min-h-[56px] flex-col items-center justify-center gap-1 px-1 py-2 text-[11px] font-medium transition-colors ${
                  active ? "text-accent" : "text-ink-subtle hover:text-ink"
                }`}
              >
                <span aria-hidden>{tab.icon}</span>
                <span className="leading-none">{tab.label}</span>
              </Link>
            </li>
          );
        })}
      </ul>
    </nav>
  );
}

const ICON_PROPS = {
  width: 22,
  height: 22,
  viewBox: "0 0 24 24",
  fill: "none",
  stroke: "currentColor",
  strokeWidth: 1.75,
  strokeLinecap: "round" as const,
  strokeLinejoin: "round" as const,
};

function BriefingIcon() {
  return (
    <svg {...ICON_PROPS}>
      <path d="M5 4h11l3 3v13a1 1 0 0 1-1 1H5a1 1 0 0 1-1-1V5a1 1 0 0 1 1-1Z" />
      <path d="M8 10h8M8 14h6" />
    </svg>
  );
}

function DashboardIcon() {
  return (
    <svg {...ICON_PROPS}>
      <path d="M4 13h5v7H4zM10 8h5v12h-5zM16 4h4v16h-4z" />
    </svg>
  );
}

function ChatIcon() {
  return (
    <svg {...ICON_PROPS}>
      <path d="M4 5h16v11H9l-4 4v-4H4z" />
    </svg>
  );
}

function PlanIcon() {
  return (
    <svg {...ICON_PROPS}>
      <circle cx="12" cy="12" r="8" />
      <path d="M12 8v4l2.5 2.5" />
    </svg>
  );
}

function ImportIcon() {
  return (
    <svg {...ICON_PROPS}>
      <path d="M12 3v11M8 10l4 4 4-4M5 21h14" />
    </svg>
  );
}
