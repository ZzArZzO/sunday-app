"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Group } from "@visx/group";
import { ParentSize } from "@visx/responsive";
import { scaleLinear } from "@visx/scale";
import { Line, LinePath } from "@visx/shape";

import { TrendArrow } from "@/components/TrendArrow";
import { fetchBenchmark } from "@/lib/api";
import { formatDual, formatPct } from "@/lib/format";
import type { BenchmarkResponse } from "@/lib/types";

const INDICES = [
  { key: "msci_world", label: "MSCI World" },
  { key: "sp500", label: "S&P 500" },
];

const HEIGHT = 200;

export function BenchmarkChart() {
  const [index, setIndex] = useState("msci_world");
  const [data, setData] = useState<BenchmarkResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    setLoading(true);
    setError(null);
    fetchBenchmark(index)
      .then((res) => {
        if (active) setData(res);
      })
      .catch((err) => {
        if (active) setError(err instanceof Error ? err.message : String(err));
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => {
      active = false;
    };
  }, [index]);

  return (
    <section className="space-y-4">
      <div className="flex flex-wrap items-baseline justify-between gap-3">
        <p className="label">Performance vs benchmark</p>
        <div className="flex gap-1">
          {INDICES.map((opt) => (
            <button
              key={opt.key}
              type="button"
              onClick={() => setIndex(opt.key)}
              className={`rounded-md px-2.5 py-1 text-xs font-medium transition-colors ${
                index === opt.key
                  ? "bg-ink text-bg"
                  : "border border-rule text-ink-muted hover:text-ink"
              }`}
            >
              {opt.label}
            </button>
          ))}
        </div>
      </div>

      <div className="card p-5">
        {loading ? (
          <div className="skeleton h-[200px] w-full" />
        ) : error ? (
          <p className="text-sm text-ink-muted">Couldn&apos;t load the comparison: {error}</p>
        ) : data && data.available ? (
          <BenchmarkBody data={data} />
        ) : (
          <div className="space-y-2 text-sm text-ink-muted">
            <p>{data?.note ?? "Benchmark comparison isn't available yet."}</p>
            {data?.note?.includes("Pro") ? (
              <Link href="/billing" className="btn btn-primary inline-flex">
                Upgrade to Pro
              </Link>
            ) : null}
          </div>
        )}
      </div>
    </section>
  );
}

function BenchmarkBody({ data }: { data: BenchmarkResponse }) {
  const diffPct = data.diff_pct !== null ? Number(data.diff_pct) : null;
  const diffClass =
    diffPct === null
      ? "text-ink-muted"
      : diffPct > 0
        ? "text-positive"
        : diffPct < 0
          ? "text-negative"
          : "text-ink-muted";

  return (
    <div className="space-y-4">
      <div style={{ height: HEIGHT }}>
        <ParentSize>
          {({ width }) => (width > 0 ? <Chart data={data} width={width} height={HEIGHT} /> : null)}
        </ParentSize>
      </div>

      <div className="flex flex-wrap items-center gap-x-6 gap-y-2 text-sm">
        <Metric label="Your portfolio (TWR)" value={data.portfolio_pct} accent="rgb(var(--accent))" />
        {data.index_available ? (
          <Metric label={data.index_name} value={data.index_pct} accent="rgb(var(--ink-subtle))" dashed />
        ) : (
          <span className="text-xs text-ink-subtle">
            {data.index_name} series unavailable right now — showing your return only.
          </span>
        )}
        {diffPct !== null ? (
          <span className="inline-flex items-center gap-1.5">
            <span className="text-ink-subtle">Difference</span>
            <span className={`inline-flex items-center gap-1 font-mono tabular-nums ${diffClass}`}>
              <TrendArrow value={diffPct} className={diffClass} />
              {diffPct > 0 ? "+" : ""}
              {formatPct(data.diff_pct!)}
              {data.diff ? ` · ${formatDual(data.diff).split(" / ")[0]}` : ""}
            </span>
          </span>
        ) : null}
      </div>

      <p className="text-xs italic text-ink-subtle">{data.disclaimer}</p>
    </div>
  );
}

function Metric({
  label,
  value,
  accent,
  dashed = false,
}: {
  label: string;
  value: string | null;
  accent: string;
  dashed?: boolean;
}) {
  return (
    <span className="inline-flex items-center gap-2">
      <svg width="18" height="8" aria-hidden>
        <line
          x1="0"
          y1="4"
          x2="18"
          y2="4"
          stroke={accent}
          strokeWidth="2"
          strokeDasharray={dashed ? "3 2" : undefined}
        />
      </svg>
      <span className="text-ink-subtle">{label}</span>
      <span className="font-mono tabular-nums text-ink">
        {value !== null ? `${Number(value) > 0 ? "+" : ""}${formatPct(value)}` : "—"}
      </span>
    </span>
  );
}

type SeriesPoint = { i: number; y: number };

function Chart({ data, width, height }: { data: BenchmarkResponse; width: number; height: number }) {
  const margin = { top: 8, right: 8, bottom: 8, left: 8 };
  const innerW = width - margin.left - margin.right;
  const innerH = height - margin.top - margin.bottom;

  const portfolio: SeriesPoint[] = data.series.map((p, i) => ({ i, y: Number(p.portfolio_twr_pct) }));
  const indexLine: SeriesPoint[] = data.series
    .map((p, i) => ({ i, y: p.index_twr_pct !== null ? Number(p.index_twr_pct) : null }))
    .filter((p): p is SeriesPoint => p.y !== null);

  const ys = [...portfolio.map((p) => p.y), ...indexLine.map((p) => p.y), 0];
  const yMin = Math.min(...ys);
  const yMax = Math.max(...ys);
  const pad = (yMax - yMin || 1) * 0.1;

  const xScale = scaleLinear({ domain: [0, Math.max(1, portfolio.length - 1)], range: [0, innerW] });
  const yScale = scaleLinear({ domain: [yMin - pad, yMax + pad], range: [innerH, 0] });

  return (
    <svg width={width} height={height}>
      <Group left={margin.left} top={margin.top}>
        {/* 0% reference line */}
        <Line
          from={{ x: 0, y: yScale(0) }}
          to={{ x: innerW, y: yScale(0) }}
          stroke="rgb(var(--rule))"
          strokeWidth={1}
          strokeDasharray="2 3"
        />
        {indexLine.length > 1 ? (
          <LinePath<SeriesPoint>
            data={indexLine}
            x={(d) => xScale(d.i)}
            y={(d) => yScale(d.y)}
            stroke="rgb(var(--ink-subtle))"
            strokeWidth={1.5}
            strokeDasharray="3 2"
          />
        ) : null}
        <LinePath<SeriesPoint>
          data={portfolio}
          x={(d) => xScale(d.i)}
          y={(d) => yScale(d.y)}
          stroke="rgb(var(--accent))"
          strokeWidth={2}
        />
      </Group>
    </svg>
  );
}
