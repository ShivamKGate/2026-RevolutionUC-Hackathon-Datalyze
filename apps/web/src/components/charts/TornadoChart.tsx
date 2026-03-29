import Plot from "react-plotly.js";
import type { Data, Layout } from "plotly.js";
import { ChartFrame } from "./ChartFrame";
import { baseLayout, chartColors } from "./plotlyTheme";
import type { TornadoFactor } from "./types";

export type TornadoChartProps = {
  factors: TornadoFactor[];
  title: string;
  className?: string;
};

export function TornadoChart({ factors, title, className }: TornadoChartProps) {
  const labels = factors.map((f) => f.label);
  const span = factors.map((f) => Math.max(0, f.high - f.low));
  const base = factors.map((f) => f.low);

  const data: Data[] = [
    {
      type: "bar",
      orientation: "h",
      name: "Range (low → high)",
      x: span,
      base,
      y: labels,
      marker: { color: chartColors.accent },
      hovertemplate:
        "%{y}<br>low: %{base}<br>high: %{customdata}<extra></extra>",
      customdata: factors.map((f) => f.high),
    } as Data,
  ];

  const layout: Partial<Layout> = baseLayout({
    title: { text: "" },
    xaxis: { title: { text: "Value" } },
    yaxis: { title: { text: "Factor" }, automargin: true },
    showlegend: false,
  });

  return (
    <ChartFrame title={title} className={className}>
      <div className="plotly-chart-host">
        <Plot
          data={data}
          layout={layout}
          style={{ width: "100%", height: Math.max(320, factors.length * 36) }}
          useResizeHandler
          config={{ displayModeBar: true, responsive: true }}
        />
      </div>
    </ChartFrame>
  );
}
