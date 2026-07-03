import { TrendArrow } from "@/components/TrendArrow";

// The single place gain/loss direction is rendered. Colour-blind-safe by
// construction: blue for up, orange for down (never green/red), and colour is
// never the only signal — every value pairs a sign-bearing label with a
// directional arrow. Flat/zero is neutral grey with no arrow.

export interface GainLossTagProps {
  /** Signed magnitude driving direction; 0 renders as flat/neutral. */
  value: number;
  /** Fully formatted text to display, e.g. "+2.4%" or "+€3,340". */
  label: string;
  size?: "sm" | "md" | "lg";
  className?: string;
}

const SIZE_STYLES: Record<NonNullable<GainLossTagProps["size"]>, { text: string; icon: number }> = {
  sm: { text: "text-xs", icon: 11 },
  md: { text: "text-sm", icon: 13 },
  lg: { text: "text-lg", icon: 16 },
};

export function GainLossTag({ value, label, size = "sm", className = "" }: GainLossTagProps) {
  const tone = value > 0 ? "text-positive" : value < 0 ? "text-negative" : "text-ink-muted";
  const { text, icon } = SIZE_STYLES[size];
  return (
    <span
      className={`inline-flex items-center gap-1 font-mono font-medium tabular-nums ${tone} ${text} ${className}`}
    >
      {value !== 0 ? <TrendArrow value={value} size={icon} /> : null}
      {label}
    </span>
  );
}
