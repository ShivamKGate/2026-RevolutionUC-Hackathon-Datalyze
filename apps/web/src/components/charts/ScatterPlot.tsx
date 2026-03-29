import Plot from "react-plotly.js";
import type { Data, Layout } from "plotly.js";
import { ChartFrame } from "./ChartFrame";
import { baseLayout, chartColors } from "./plotlyTheme";
import type { ScatterPoint } from "./types";

export type ScatterPlotProps = {
  points: ScatterPoint[];
  xLabel: string;
  yLabel: string;
  title: string;
  className?: string;
};

export function ScatterPlot({
  points,
  xLabel,
  yLabel,
  title,
  className,
}: ScatterPlotProps) {
  const x = points.map((p) => p.x);
  const y = points.map((p) => p.y);
  const text = points.map((p) => p.label ?? "");
  const colors = points.map((p) => p.color ?? chartColors.accent);

  const data: Data[] = [
    {
      type: "scatter",
      mode: "markers",
      x,
      y,
      text,
      marker: {
        size: 10,
        color: colors,
        opacity: 0.9,
        line: { color: "rgba(15, 23, 42, 0.95)", width: 1 },
      },
      hovertemplate:
        "%{text}<br>" +
        `${xLabel}: %{x:.4f}<br>` +
        `${yLabel}: %{y:.4f}<extra></extra>`,
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
          style={{ width: "100%", height: 380 }}
          useResizeHandler
          config={{ displayModeBar: true, responsive: true }}
        />
      </div>
    </ChartFrame>
  );
}
