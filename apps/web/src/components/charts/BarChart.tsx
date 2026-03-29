import Plot from "react-plotly.js";
import type { Data, Layout } from "plotly.js";
import { ChartFrame } from "./ChartFrame";
import { baseLayout, chartColors } from "./plotlyTheme";

export type BarChartProps = {
  categories: string[];
  values: number[];
  title: string;
  horizontal?: boolean;
  className?: string;
};

export function BarChart({
  categories,
  values,
  title,
  horizontal = false,
  className,
}: BarChartProps) {
  const data: Data[] = horizontal
    ? [
        {
          type: "bar",
          orientation: "h",
          x: values,
          y: categories,
          marker: { color: chartColors.series[0] },
        },
      ]
    : [
        {
          type: "bar",
          x: categories,
          y: values,
          marker: { color: chartColors.series[0] },
        },
      ];

  const layout: Partial<Layout> = baseLayout({
    title: { text: "" },
    xaxis: horizontal ? { title: { text: "Value" } } : { title: { text: "Category" } },
    yaxis: horizontal ? { title: { text: "Category" } } : { title: { text: "Value" } },
  });

  return (
    <ChartFrame title={title} className={className}>
      <div className="plotly-chart-host">
        <Plot
          data={data}
          layout={layout}
          style={{ width: "100%", height: 360 }}
          useResizeHandler
          config={{ displayModeBar: true, responsive: true }}
        />
      </div>
    </ChartFrame>
  );
}
