import { BriefingView } from "@/components/BriefingView";
import { fetchBriefing } from "@/lib/api";

export const dynamic = "force-dynamic";

export default async function BriefingPage() {
  let briefing;
  try {
    briefing = await fetchBriefing();
  } catch (err) {
    return (
      <div className="rounded-md border border-negative/30 bg-negative/5 p-6 text-sm text-negative">
        <p className="font-medium">Couldn&apos;t load briefing.</p>
        <p className="mt-2">{err instanceof Error ? err.message : String(err)}</p>
      </div>
    );
  }

  return <BriefingView briefing={briefing} />;
}
