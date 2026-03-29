import Plot from "react-plotly.js";
import type { Data, Layout } from "plotly.js";
import { ChartFrame } from "./ChartFrame";
import { baseLayout, chartColors } from "./plotlyTheme";

export type ParetoChartProps = {
  categories: string[];
  values: number[];
  title: string;
  className?: string;
};

export function ParetoChart({ categories, values, title, className }: ParetoChartProps) {
  const total = values.reduce((a, b) => a + b, 0) || 1;
  let acc = 0;
  const cumulativePct = values.map((v) => {
    acc += v;
    return (acc / total) * 100;
  });

  const data: Data[] = [
    {
      type: "bar",
      name: "Value",
      x: categories,
      y: values,
      marker: { color: chartColors.series[0] },
    },
    {
      type: "scatter",
      name: "Cumulative %",
      x: categories,
      y: cumulativePct,
      yaxis: "y2",
      mode: "lines+markers",
      line: { color: chartColors.series[1], width: 2 },
      marker: { size: 6 },
    },
  ];

  const layout: Partial<Layout> = baseLayout({
    title: { text: "" },
    xaxis: { title: { text: "Category" } },
    yaxis: { title: { text: "Value" }, rangemode: "tozero" },
    yaxis2: {
      title: { text: "Cumulative %" },
      overlaying: "y",
      side: "right",
      range: [0, 105],
      showgrid: false,
    },
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
