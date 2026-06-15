"use client";

import { BriefingActions } from "@/components/BriefingActions";
import { BriefingView } from "@/components/BriefingView";
import { BiometricLockToggle } from "@/components/BiometricLockToggle";
import { EventsCard } from "@/components/EventsCard";
import { PushPrimer } from "@/components/PushPrimer";
import { WeeklyOptInToggle } from "@/components/WeeklyOptInToggle";
import { fetchBriefing } from "@/lib/api";
import { useAsync } from "@/lib/useAsync";

export default function BriefingPage() {
  const { data: briefing, loading, error } = useAsync(fetchBriefing);

  if (loading) {
    return (
      <div className="container-prose -mx-6 space-y-6 sm:mx-0">
        <div className="skeleton h-12 w-1/2" />
        <div className="skeleton h-40 w-full" />
      </div>
    );
  }

  if (error || !briefing) {
    return (
      <div className="card border-negative/30 bg-negative-subtle/40 p-5">
        <p className="font-medium text-negative">Couldn&apos;t load briefing</p>
        <p className="mt-2 text-sm text-ink">{error}</p>
      </div>
    );
  }

  return (
    <div className="container-prose -mx-6 space-y-12 sm:mx-0">
      <BriefingView briefing={briefing} />
      <div className="space-y-3">
        <BriefingActions />
        <WeeklyOptInToggle />
        <PushPrimer />
        <BiometricLockToggle />
      </div>
      <EventsCard />
    </div>
  );
}
