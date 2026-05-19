import Link from "next/link";

const links = [
  { href: "/", label: "Home" },
  { href: "/upload", label: "Upload" },
  { href: "/dashboard", label: "Dashboard" },
  { href: "/briefing", label: "Briefing" },
];

export function NavBar() {
  return (
    <nav className="border-b border-ink/10 bg-paper-card">
      <div className="container-narrow flex items-center justify-between py-4">
        <Link href="/" className="text-lg font-semibold">
          Sunday
        </Link>
        <ul className="flex gap-6 text-sm">
          {links.map((link) => (
            <li key={link.href}>
              <Link href={link.href} className="text-ink-muted hover:text-ink">
                {link.label}
              </Link>
            </li>
          ))}
        </ul>
      </div>
    </nav>
  );
}
