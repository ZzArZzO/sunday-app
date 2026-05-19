import { BriefingView } from "@/components/BriefingView";
import { fetchBriefing } from "@/lib/api";

export const dynamic = "force-dynamic";

export default async function BriefingPage() {
  let briefing;
  try {
    briefing = await fetchBriefing();
  } catch (err) {
    return (
      <div className="card border-negative/30 bg-negative-subtle/40 p-5">
        <p className="font-medium text-negative">Couldn&apos;t load briefing</p>
        <p className="mt-2 text-sm text-ink">
          {err instanceof Error ? err.message : String(err)}
        </p>
      </div>
    );
  }

  return (
    <div className="container-prose -mx-6 sm:mx-0">
      <BriefingView briefing={briefing} />
    </div>
  );
}
