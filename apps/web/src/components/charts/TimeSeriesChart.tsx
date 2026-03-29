import Plot from "react-plotly.js";
import type { Data, Layout } from "plotly.js";
import { ChartFrame } from "./ChartFrame";
import { baseLayout, chartColors } from "./plotlyTheme";
import type { TimeSeriesPoint } from "./types";

export type TimeSeriesChartProps = {
  series: TimeSeriesPoint[];
  title: string;
  showConfidenceBands?: boolean;
  className?: string;
};

export function TimeSeriesChart({
  series,
  title,
  showConfidenceBands = false,
  className,
}: TimeSeriesChartProps) {
  const dates = series.map((p) => p.date);
  const values = series.map((p) => p.value);

  const traces: Data[] = [];

  if (
    showConfidenceBands &&
    series.some((p) => p.lower != null && p.upper != null)
  ) {
    const upper = series.map((p) => p.upper ?? p.value);
    const lower = series.map((p) => p.lower ?? p.value);
    traces.push({
      type: "scatter",
      mode: "lines",
      name: "Upper",
      x: dates,
      y: upper,
      line: { width: 0 },
      showlegend: false,
      hoverinfo: "skip",
    });
    traces.push({
      type: "scatter",
      mode: "lines",
      name: "Confidence band",
      x: dates,
      y: lower,
      line: { width: 0 },
      fillcolor: "rgba(59, 130, 246, 0.22)",
      fill: "tonexty",
      showlegend: true,
    });
  }

  traces.push({
    type: "scatter",
    mode: "lines",
    name: "Series",
    x: dates,
    y: values,
    line: { color: chartColors.accent, width: 2 },
  });

  const layout: Partial<Layout> = baseLayout({
    title: { text: "" },
    xaxis: { title: { text: "Date" } },
    yaxis: { title: { text: "Value" } },
  });

  return (
    <ChartFrame title={title} className={className}>
      <div className="plotly-chart-host">
        <Plot
          data={traces}
          layout={layout}
          style={{ width: "100%", height: 360 }}
          useResizeHandler
          config={{ displayModeBar: true, responsive: true }}
        />
      </div>
    </ChartFrame>
  );
}
