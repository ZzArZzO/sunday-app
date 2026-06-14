import Link from "next/link";

import { AuthStatus } from "@/components/AuthStatus";
import { ThemeToggle } from "@/components/ThemeToggle";

const links = [
  { href: "/", label: "Home" },
  { href: "/upload", label: "Import" },
  { href: "/dashboard", label: "Dashboard" },
  { href: "/plan", label: "Plan" },
  { href: "/briefing", label: "Briefing" },
  { href: "/assistant", label: "Assistant" },
];

/**
 * Sticky modern navbar with subtle blur and bordered base. Wordmark on left,
 * link group + theme toggle on right. On narrow screens the link group becomes
 * a horizontally-scrollable rail to keep all destinations one-tap reachable.
 */
export function NavBar() {
  return (
    <header className="sticky top-0 z-40 border-b border-rule bg-bg/80 backdrop-blur-md">
      <div className="container-narrow flex h-14 items-center justify-between gap-2">
        <Link href="/" className="group inline-flex flex-none items-center gap-2">
          <Logo />
          <span className="font-sans text-base font-semibold tracking-tight text-ink group-hover:text-accent">
            Sunday
          </span>
        </Link>
        <div className="flex min-w-0 flex-1 items-center justify-end gap-1 sm:gap-2">
          <nav className="hidden min-w-0 flex-1 md:block md:flex-none">
            <ul className="flex items-center gap-1 overflow-x-auto scrollbar-none">
              {links.map((link) => (
                <li key={link.href} className="flex-none">
                  <Link
                    href={link.href}
                    className="rounded-md px-2.5 py-1.5 text-sm font-medium text-ink-muted transition-colors duration-200 ease-out hover:bg-surface-2 hover:text-ink sm:px-3"
                  >
                    {link.label}
                  </Link>
                </li>
              ))}
            </ul>
          </nav>
          <div className="ml-1 flex-none border-l border-rule pl-1 sm:ml-2 sm:pl-2">
            <AuthStatus />
          </div>
          <div className="flex-none">
            <ThemeToggle />
          </div>
        </div>
      </div>
    </header>
  );
}

function Logo() {
  return (
    <span
      aria-hidden
      className="flex h-7 w-7 items-center justify-center rounded-md bg-ink text-bg shadow-soft"
    >
      <svg viewBox="0 0 24 24" width="14" height="14" fill="none">
        <circle cx="12" cy="12" r="6" fill="currentColor" />
        <circle cx="16" cy="9" r="3" fill="rgb(var(--bg))" />
      </svg>
    </span>
  );
}
