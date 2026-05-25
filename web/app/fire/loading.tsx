export default function Loading() {
  return (
    <div className="space-y-8">
      <div className="skeleton h-12 w-2/3" />
      <div className="skeleton h-48 w-full" />
      <div className="skeleton h-72 w-full" />
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <div className="skeleton h-32 w-full" />
        <div className="skeleton h-32 w-full" />
        <div className="skeleton h-32 w-full" />
        <div className="skeleton h-32 w-full" />
      </div>
    </div>
  );
}
