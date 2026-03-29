import Plot from "react-plotly.js";
import type { Data, Layout } from "plotly.js";
import { ChartFrame } from "./ChartFrame";
import { baseLayout, chartColors } from "./plotlyTheme";
import type { WaterfallStep } from "./types";

export type WaterfallChartProps = {
  steps: WaterfallStep[];
  title: string;
  className?: string;
};

function toMeasure(t: WaterfallStep["type"]): "relative" | "total" {
  return t === "total" ? "total" : "relative";
}

export function WaterfallChart({ steps, title, className }: WaterfallChartProps) {
  const x = steps.map((s) => s.label);
  const y = steps.map((s) => {
    if (s.type === "decrease") return -Math.abs(s.value);
    return Math.abs(s.value);
  });
  const measure = steps.map((s) => toMeasure(s.type));

  const increasing = { marker: { color: chartColors.positive } };
  const decreasing = { marker: { color: chartColors.negative } };
  const totals = { marker: { color: chartColors.accent } };

  const data: Data[] = [
    {
      type: "waterfall",
      orientation: "v",
      x,
      y,
      measure: measure as ("relative" | "total")[],
      increasing,
      decreasing,
      totals,
      connector: { line: { color: "rgba(148, 163, 184, 0.5)" } },
    } as Data,
  ];

  const layout: Partial<Layout> = baseLayout({
    title: { text: "" },
    xaxis: { title: { text: "Step" } },
    yaxis: { title: { text: "Value" } },
    showlegend: false,
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
