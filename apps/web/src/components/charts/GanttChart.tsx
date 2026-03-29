import Plot from "react-plotly.js";
import type { Data, Layout } from "plotly.js";
import { ChartFrame } from "./ChartFrame";
import { baseLayout, chartColors } from "./plotlyTheme";
import type { GanttTask } from "./types";

export type GanttChartProps = {
  tasks: GanttTask[];
  title: string;
  className?: string;
};

function parseTime(s: string): number {
  const t = Date.parse(s);
  return Number.isFinite(t) ? t : 0;
}

export function GanttChart({ tasks, title, className }: GanttChartProps) {
  const labels = tasks.map((t) => t.name);
  const start = tasks.map((t) => parseTime(t.start));
  const end = tasks.map((t) => parseTime(t.end));
  const duration = end.map((e, i) => Math.max(0, e - start[i]));

  const data: Data[] = [
    {
      type: "bar",
      orientation: "h",
      y: labels,
      x: duration,
      base: start,
      marker: { color: chartColors.accent },
      hovertemplate:
        "%{y}<br>Start: %{base|%Y-%m-%d}<br>End: %{customdata}<extra></extra>",
      customdata: end.map((e) => new Date(e).toISOString().slice(0, 10)),
    } as Data,
  ];

  const layout: Partial<Layout> = baseLayout({
    title: { text: "" },
    xaxis: {
      type: "date",
      title: { text: "Timeline" },
    },
    yaxis: { title: { text: "Task" }, automargin: true },
    showlegend: false,
  });

  const height = Math.max(320, tasks.length * 40);

  return (
    <ChartFrame title={title} className={className}>
      <div className="plotly-chart-host">
        <Plot
          data={data}
          layout={layout}
          style={{ width: "100%", height }}
          useResizeHandler
          config={{ displayModeBar: true, responsive: true }}
        />
      </div>
    </ChartFrame>
  );
}
