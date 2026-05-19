export default function BriefingLoading() {
  return (
    <div className="container-prose -mx-6 space-y-12 sm:mx-0">
      <header className="space-y-2">
        <div className="skeleton h-3 w-56" />
        <div className="skeleton h-10 w-3/4" />
      </header>

      <section className="card space-y-4 p-8">
        <div className="skeleton h-3 w-24" />
        <div className="skeleton h-16 w-2/3" />
        <div className="skeleton h-4 w-1/2" />
      </section>

      {Array.from({ length: 3 }).map((_, i) => (
        <section key={i} className="space-y-3">
          <div className="skeleton h-3 w-24" />
          <div className="skeleton h-8 w-2/3" />
          <div className="space-y-2">
            <div className="skeleton h-4 w-full" />
            <div className="skeleton h-4 w-11/12" />
            <div className="skeleton h-4 w-3/4" />
          </div>
        </section>
      ))}
    </div>
  );
}
