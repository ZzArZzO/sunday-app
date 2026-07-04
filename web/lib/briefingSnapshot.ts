// Static issue metadata for the briefing letter. Portfolio figures live in
// portfolioSnapshot.ts and are shared across screens; this module holds only
// what's specific to a given edition of the letter itself.

export interface BriefingIssue {
  weekOf: string;
  issueNumber: number;
  readMinutes: number;
  dateline: string;
  generatedAt: string;
}

export const BRIEFING_ISSUE: BriefingIssue = {
  weekOf: "30 Jun",
  issueNumber: 12,
  readMinutes: 3,
  dateline: "Sunday, 30 June 2026",
  generatedAt: "30 June 2026, 18:04",
};
