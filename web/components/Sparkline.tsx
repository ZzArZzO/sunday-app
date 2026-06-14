// Tiny zero-dependency SVG sparkline. Renders a small trend line beside
// briefing prose when a section supplies a `spark` series. Direction is
// conveyed by colour (colour-blind-safe positive/negative tokens) AND by the
// implicit slope; it is decorative context, never the sole carrier of meaning.

type SparklineProps = {
  values: number[];
  width?: number;
  height?: number;
  className?: string;
};

export function Sparkline({ values, width = 96, height = 28, className = "" }: SparklineProps) {
  if (values.length < 2) return null;

  const min = Math.min(...values);
  const max = Math.max(...values);
  const span = max - min || 1;
  const stepX = width / (values.length - 1);

  const points = values.map((v, i) => {
    const x = i * stepX;
    const y = height - ((v - min) / span) * height;
    return `${x.toFixed(2)},${y.toFixed(2)}`;
  });

  const rising = values[values.length - 1] >= values[0];
  const stroke = rising ? "rgb(var(--positive))" : "rgb(var(--negative))";

  return (
    <svg
      aria-hidden
      viewBox={`0 0 ${width} ${height}`}
      width={width}
      height={height}
      fill="none"
      className={className}
      preserveAspectRatio="none"
    >
      <polyline
        points={points.join(" ")}
        stroke={stroke}
        strokeWidth="1.5"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}
