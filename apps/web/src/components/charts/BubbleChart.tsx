import Plot from "react-plotly.js";
import type { Data, Layout } from "plotly.js";
import { ChartFrame } from "./ChartFrame";
import { baseLayout, chartColors } from "./plotlyTheme";
import type { BubblePoint } from "./types";

export type BubbleChartProps = {
  points: BubblePoint[];
  xLabel: string;
  yLabel: string;
  title: string;
  className?: string;
};

function scaleSizes(sizes: number[]): number[] {
  if (sizes.length === 0) return [];
  const minS = Math.min(...sizes);
  const maxS = Math.max(...sizes);
  const lo = 8;
  const hi = 48;
  if (maxS === minS) return sizes.map(() => (lo + hi) / 2);
  return sizes.map((s) => lo + ((s - minS) / (maxS - minS)) * (hi - lo));
}

export function BubbleChart({
  points,
  xLabel,
  yLabel,
  title,
  className,
}: BubbleChartProps) {
  const x = points.map((p) => p.x);
  const y = points.map((p) => p.y);
  const text = points.map((p) => p.label);
  const sizes = scaleSizes(points.map((p) => p.size));
  const colors = points.map(
    (p) => p.color ?? chartColors.accent,
  );

  const data: Data[] = [
    {
      type: "scatter",
      mode: "markers",
      x,
      y,
      text,
      marker: {
        size: sizes,
        color: colors,
        opacity: 0.85,
        line: { color: "rgba(15, 23, 42, 0.9)", width: 1 },
      },
      hovertemplate:
        "<b>%{text}</b><br>" +
        `${xLabel}: %{x:.3f}<br>` +
        `${yLabel}: %{y:.3f}<extra></extra>`,
    },
  ];

  const layout: Partial<Layout> = baseLayout({
    title: { text: "" },
    xaxis: { title: { text: xLabel } },
    yaxis: { title: { text: yLabel } },
  });

  return (
    <ChartFrame title={title} className={className}>
      <div className="plotly-chart-host">
        <Plot
          data={data}
          layout={layout}
          style={{ width: "100%", height: 400 }}
          useResizeHandler
          config={{ displayModeBar: true, responsive: true }}
        />
      </div>
    </ChartFrame>
  );
}
