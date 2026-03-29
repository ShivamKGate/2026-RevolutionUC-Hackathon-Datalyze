import Plot from "react-plotly.js";
import type { ColorScale, Data, Layout } from "plotly.js";
import { ChartFrame } from "./ChartFrame";
import { baseLayout } from "./plotlyTheme";

export type HeatmapChartProps = {
  rows: string[];
  cols: string[];
  /** values[rowIndex][colIndex] */
  values: number[][];
  title: string;
  colorScale?: ColorScale;
  className?: string;
};

export function HeatmapChart({
  rows,
  cols,
  values,
  title,
  colorScale,
  className,
}: HeatmapChartProps) {
  const data: Data[] = [
    {
      type: "heatmap",
      x: cols,
      y: rows,
      z: values,
      colorscale: colorScale ?? "Blues",
      hoverongaps: false,
    },
  ];

  const layout: Partial<Layout> = baseLayout({
    title: { text: "" },
    xaxis: { title: { text: "" }, side: "bottom" },
    yaxis: { title: { text: "" }, autorange: "reversed" },
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
