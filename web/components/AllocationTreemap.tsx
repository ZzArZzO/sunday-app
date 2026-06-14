"use client";

import { Group } from "@visx/group";
import { Treemap, hierarchy, treemapSquarify } from "@visx/hierarchy";
import { ParentSize } from "@visx/responsive";

import type { PositionView } from "@/lib/types";
import { formatDual, formatPct } from "@/lib/format";
import { DEFAULT_LOCALE, type SupportedLocale } from "@/lib/locale";

// Per-holding treemap: tile area ∝ market value, tile colour = gain/loss
// (colour-blind-safe blue/orange). Spots concentration and which names carry
// the portfolio at a glance. The sortable holdings table is the accessible
// data equivalent, so this is decorative — labelled for screen readers.

const HEIGHT = 280;

type Leaf = {
  ticker: string;
  value: number;
  pnlPct: number;
  marketValue: PositionView["market_value"];
  pnl: PositionView["unrealised_pnl"];
};

type TreeData = { ticker: string; children: Leaf[] };

function fillFor(pnlPct: number): string {
  if (pnlPct > 0) return "rgb(var(--positive))";
  if (pnlPct < 0) return "rgb(var(--negative))";
  return "rgb(var(--ink-subtle))";
}

function toLeaf(p: PositionView): Leaf {
  const cost = Number(p.cost_basis.eur);
  const pnl = Number(p.unrealised_pnl.eur);
  return {
    ticker: p.ticker,
    value: Math.max(0, Number(p.market_value.eur)),
    pnlPct: cost > 0 ? (pnl / cost) * 100 : 0,
    marketValue: p.market_value,
    pnl: p.unrealised_pnl,
  };
}

export function AllocationTreemap({
  positions,
  locale = DEFAULT_LOCALE,
}: {
  positions: PositionView[];
  locale?: SupportedLocale;
}) {
  const leaves = positions.map(toLeaf).filter((l) => l.value > 0);
  if (leaves.length === 0) {
    return <p className="text-sm text-ink-muted">No holdings to chart yet.</p>;
  }

  const ariaLabel =
    "Holdings by market value: " +
    [...leaves]
      .sort((a, b) => b.value - a.value)
      .map((l) => `${l.ticker} ${formatPct(String(l.pnlPct), locale)}`)
      .join(", ");

  const data: TreeData = { ticker: "root", children: leaves };

  return (
    <div role="img" aria-label={ariaLabel} style={{ height: HEIGHT }}>
      <ParentSize>
        {({ width }) =>
          width > 0 ? (
            <TreemapSvg data={data} width={width} height={HEIGHT} locale={locale} />
          ) : null
        }
      </ParentSize>
    </div>
  );
}

function TreemapSvg({
  data,
  width,
  height,
  locale,
}: {
  data: TreeData;
  width: number;
  height: number;
  locale: SupportedLocale;
}) {
  const root = hierarchy<TreeData | Leaf>(data, (d) =>
    "children" in d ? d.children : null,
  )
    .sum((d) => ("value" in d ? d.value : 0))
    .sort((a, b) => (b.value ?? 0) - (a.value ?? 0));

  return (
    <svg width={width} height={height}>
      <Treemap<TreeData | Leaf>
        root={root}
        size={[width, height]}
        tile={treemapSquarify}
        round
      >
        {(treemap) => (
          <Group>
            {treemap
              .descendants()
              .filter((node) => node.depth > 0)
              .map((node, i) => {
                const leaf = node.data as Leaf;
                const w = node.x1 - node.x0;
                const h = node.y1 - node.y0;
                const showLabel = w > 52 && h > 30;
                return (
                  <Group key={`tile-${i}`} top={node.y0} left={node.x0}>
                    <rect
                      width={w}
                      height={h}
                      rx={4}
                      fill={fillFor(leaf.pnlPct)}
                      fillOpacity={0.85}
                      stroke="rgb(var(--bg))"
                      strokeWidth={2}
                    >
                      <title>{`${leaf.ticker} · ${formatDual(leaf.marketValue, locale)} · ${
                        leaf.pnlPct >= 0 ? "+" : ""
                      }${formatPct(String(leaf.pnlPct), locale)}`}</title>
                    </rect>
                    {showLabel ? (
                      <text
                        x={6}
                        y={18}
                        fontSize={12}
                        fontWeight={600}
                        fill="white"
                        className="font-sans"
                      >
                        {leaf.ticker}
                      </text>
                    ) : null}
                  </Group>
                );
              })}
          </Group>
        )}
      </Treemap>
    </svg>
  );
}
