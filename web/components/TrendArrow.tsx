// Small directional arrow used next to gain/loss figures so direction is
// conveyed by shape as well as colour (colour-blind accessibility). Flat values
// render nothing — the sign on the number carries it.

type TrendArrowProps = {
  value: number;
  className?: string;
  size?: number;
};

export function TrendArrow({ value, className = "", size = 12 }: TrendArrowProps) {
  if (value === 0) return null;
  const up = value > 0;
  return (
    <svg
      aria-hidden
      viewBox="0 0 24 24"
      width={size}
      height={size}
      fill="none"
      stroke="currentColor"
      strokeWidth="2.5"
      strokeLinecap="round"
      strokeLinejoin="round"
      className={`inline-block ${className}`}
    >
      {up ? <path d="M7 14l5-5 5 5" /> : <path d="M7 10l5 5 5-5" />}
    </svg>
  );
}
