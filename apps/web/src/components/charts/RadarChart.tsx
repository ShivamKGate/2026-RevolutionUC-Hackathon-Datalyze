import Plot from "react-plotly.js";
import type { Data, Layout } from "plotly.js";
import { ChartFrame } from "./ChartFrame";
import { baseLayout, chartColors } from "./plotlyTheme";

export type RadarDimension = {
  label: string;
  current: number;
  predicted: number;
};

export type RadarChartProps = {
  dimensions: RadarDimension[];
  title: string;
  className?: string;
};

export function RadarChart({ dimensions, title, className }: RadarChartProps) {
  const theta = dimensions.map((d) => d.label);
  const data: Data[] = [
    {
      type: "scatterpolar",
      r: dimensions.map((d) => d.current),
      theta,
      fill: "toself",
      name: "Current",
      line: { color: chartColors.accent },
      fillcolor: "rgba(59, 130, 246, 0.25)",
    },
    {
      type: "scatterpolar",
      r: dimensions.map((d) => d.predicted),
      theta,
      fill: "toself",
      name: "Predicted",
      line: { color: chartColors.series[1], dash: "dash" },
      fillcolor: "rgba(168, 85, 247, 0.15)",
    },
  ];

  const layout: Partial<Layout> = baseLayout({
    title: { text: "" },
    polar: {
      bgcolor: "#0f172a",
      radialaxis: {
        visible: true,
        gridcolor: "rgba(51, 65, 85, 0.8)",
        linecolor: "rgba(51, 65, 85, 0.8)",
      },
      angularaxis: {
        gridcolor: "rgba(51, 65, 85, 0.8)",
        linecolor: "rgba(51, 65, 85, 0.8)",
      },
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
