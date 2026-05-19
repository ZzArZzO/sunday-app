export default function DashboardLoading() {
  return (
    <div className="space-y-12">
      <header className="space-y-4">
        <div className="skeleton h-3 w-44" />
        <div className="skeleton h-14 w-2/3" />
        <div className="flex flex-wrap gap-6">
          <div className="skeleton h-4 w-40" />
          <div className="skeleton h-4 w-40" />
          <div className="skeleton h-4 w-28" />
        </div>
      </header>

      <section className="space-y-4">
        <div className="skeleton h-3 w-32" />
        <ul className="grid grid-cols-2 gap-3 sm:grid-cols-4">
          {Array.from({ length: 4 }).map((_, i) => (
            <li key={i} className="card h-20" />
          ))}
        </ul>
      </section>

      <section className="space-y-4">
        <div className="skeleton h-3 w-36" />
        <div className="grid gap-3 sm:grid-cols-2">
          {Array.from({ length: 2 }).map((_, i) => (
            <div key={i} className="card h-24" />
          ))}
        </div>
      </section>

      <section className="space-y-4">
        <div className="skeleton h-3 w-28" />
        <div className="card h-80" />
      </section>
    </div>
  );
}
