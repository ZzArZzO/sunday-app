import type { FireTimelinePoint } from "@/lib/types";
import { formatEur } from "@/lib/format";

interface FireTimelineProps {
  points: FireTimelinePoint[];
  fullFireEur: string;
  coastFireEur: string;
}

/**
 * Pure-SVG net-worth projection chart. Renders the 40-year trajectory with
 * horizontal threshold lines for Coast and Full FIRE. No external chart lib.
 */
export function FireTimeline({ points, fullFireEur, coastFireEur }: FireTimelineProps) {
  if (points.length === 0) {
    return (
      <div className="card p-5">
        <p className="text-sm text-ink-muted">No projection available.</p>
      </div>
    );
  }

  const width = 800;
  const height = 280;
  const padX = 56;
  const padY = 24;

  const values = points.map((p) => Number(p.projected_net_worth_eur));
  const fullFire = Number(fullFireEur);
  const coastFire = Number(coastFireEur);
  const maxValue = Math.max(...values, fullFire, coastFire) * 1.05;
  const minOffset = points[0].year_offset;
  const maxOffset = points[points.length - 1].year_offset;

  const xFor = (offset: number) =>
    padX + ((offset - minOffset) / Math.max(maxOffset - minOffset, 1)) * (width - padX * 2);
  const yFor = (value: number) =>
    height - padY - (value / Math.max(maxValue, 1)) * (height - padY * 2);

  const linePath = points
    .map((p, idx) => {
      const cmd = idx === 0 ? "M" : "L";
      return `${cmd} ${xFor(p.year_offset).toFixed(2)} ${yFor(Number(p.projected_net_worth_eur)).toFixed(2)}`;
    })
    .join(" ");

  const areaPath = `${linePath} L ${xFor(maxOffset).toFixed(2)} ${height - padY} L ${xFor(minOffset).toFixed(2)} ${height - padY} Z`;

  const fullFireY = yFor(fullFire);
  const coastFireY = yFor(coastFire);
  const fullFireReached = points.find((p) => p.is_full_fire);
  const coastFireReached = points.find((p) => p.is_coast_fire);

  return (
    <div className="card overflow-hidden p-5 sm:p-6">
      <header className="flex items-baseline justify-between">
        <p className="label">40-year projection</p>
        <p className="font-mono text-xs text-ink-subtle">Real EUR, after inflation</p>
      </header>

      <div className="mt-4 overflow-x-auto">
        <svg
          viewBox={`0 0 ${width} ${height}`}
          className="block h-auto w-full min-w-[640px]"
          role="img"
          aria-label="FIRE net worth projection over 40 years"
        >
          <defs>
            <linearGradient id="fire-area" x1="0" x2="0" y1="0" y2="1">
              <stop offset="0%" stopColor="rgb(var(--accent))" stopOpacity="0.32" />
              <stop offset="100%" stopColor="rgb(var(--accent))" stopOpacity="0" />
            </linearGradient>
          </defs>

          {[0.25, 0.5, 0.75, 1].map((t) => {
            const y = padY + t * (height - padY * 2);
            return (
              <line
                key={`grid-${t}`}
                x1={padX}
                x2={width - padX}
                y1={y}
                y2={y}
                stroke="rgb(var(--rule))"
                strokeDasharray="3 4"
                opacity="0.7"
              />
            );
          })}

          <line
            x1={padX}
            x2={width - padX}
            y1={fullFireY}
            y2={fullFireY}
            stroke="rgb(var(--accent))"
            strokeWidth="1.5"
            strokeDasharray="6 4"
          />
          <text
            x={width - padX}
            y={fullFireY - 6}
            textAnchor="end"
            className="fill-current font-mono text-[10px]"
            fill="rgb(var(--accent))"
          >
            Full FIRE · {formatEur(fullFireEur)}
          </text>

          <line
            x1={padX}
            x2={width - padX}
            y1={coastFireY}
            y2={coastFireY}
            stroke="rgb(var(--positive))"
            strokeWidth="1"
            strokeDasharray="2 4"
          />
          <text
            x={width - padX}
            y={coastFireY - 6}
            textAnchor="end"
            className="fill-current font-mono text-[10px]"
            fill="rgb(var(--positive))"
          >
            Coast FIRE · {formatEur(coastFireEur)}
          </text>

          <path d={areaPath} fill="url(#fire-area)" />
          <path d={linePath} fill="none" stroke="rgb(var(--ink))" strokeWidth="2" />

          {fullFireReached ? (
            <g>
              <circle
                cx={xFor(fullFireReached.year_offset)}
                cy={yFor(Number(fullFireReached.projected_net_worth_eur))}
                r="4"
                fill="rgb(var(--accent))"
              />
              <text
                x={xFor(fullFireReached.year_offset) + 8}
                y={yFor(Number(fullFireReached.projected_net_worth_eur)) - 8}
                className="fill-current font-mono text-[10px]"
                fill="rgb(var(--ink))"
              >
                +{fullFireReached.year_offset} yrs
              </text>
            </g>
          ) : null}

          {coastFireReached && (!fullFireReached || coastFireReached.year_offset < fullFireReached.year_offset) ? (
            <circle
              cx={xFor(coastFireReached.year_offset)}
              cy={yFor(Number(coastFireReached.projected_net_worth_eur))}
              r="3"
              fill="rgb(var(--positive))"
            />
          ) : null}

          {[0, 10, 20, 30, 40].map((offset) =>
            offset <= maxOffset ? (
              <text
                key={`xlabel-${offset}`}
                x={xFor(offset)}
                y={height - 4}
                textAnchor="middle"
                className="fill-current font-mono text-[10px]"
                fill="rgb(var(--ink-subtle))"
              >
                +{offset}y
              </text>
            ) : null,
          )}
        </svg>
      </div>
    </div>
  );
}
