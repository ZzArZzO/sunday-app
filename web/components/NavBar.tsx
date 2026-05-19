import Link from "next/link";

import { ThemeToggle } from "@/components/ThemeToggle";

const links = [
  { href: "/", label: "Home" },
  { href: "/upload", label: "Import" },
  { href: "/dashboard", label: "Dashboard" },
  { href: "/briefing", label: "Briefing" },
];

/**
 * Sticky modern navbar with subtle blur and bordered base. Wordmark on left,
 * link group + theme toggle on right.
 */
export function NavBar() {
  return (
    <header className="sticky top-0 z-40 border-b border-rule bg-bg/80 backdrop-blur-md">
      <div className="container-narrow flex h-14 items-center justify-between">
        <Link href="/" className="group inline-flex items-center gap-2">
          <Logo />
          <span className="font-sans text-base font-semibold tracking-tight text-ink group-hover:text-accent">
            Sunday
          </span>
        </Link>
        <div className="flex items-center gap-1 sm:gap-2">
          <nav>
            <ul className="flex items-center gap-1">
              {links.map((link) => (
                <li key={link.href}>
                  <Link
                    href={link.href}
                    className="rounded-md px-3 py-1.5 text-sm font-medium text-ink-muted transition-colors duration-200 ease-out hover:bg-surface-2 hover:text-ink"
                  >
                    {link.label}
                  </Link>
                </li>
              ))}
            </ul>
          </nav>
          <div className="ml-2 border-l border-rule pl-2">
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
