import Plot from "react-plotly.js";
import type { Data, Layout } from "plotly.js";
import { ChartFrame, baseLayout, chartColors } from "../../charts";
import type { Anomaly } from "../types";

type Props = {
  anomalies?: Anomaly[];
};

export function AnomalyTimeline({ anomalies }: Props) {
  if (!anomalies || anomalies.length === 0) return null;

  const dates = anomalies.map((a) => a.date);
  const actual = anomalies.map((a) => a.actual);
  const expected = anomalies.map((a) => a.expected);

  const data: Data[] = [
    {
      type: "scatter",
      mode: "text+markers",
      name: "Actual",
      x: dates,
      y: actual,
      text: anomalies.map((a) => a.metric),
      textposition: "top center",
      textfont: { size: 10, color: "#94a3b8" },
      marker: {
        size: 12,
        color: chartColors.negative,
        symbol: "diamond",
      },
      hovertemplate: anomalies.map(
        (a) =>
          `<b>${a.metric}</b><br>` +
          `Date: ${a.date}<br>` +
          `Expected: ${a.expected}<br>` +
          `Actual: ${a.actual}<br>` +
          `Cause: ${a.root_cause}<extra></extra>`
      ),
    },
    {
      type: "scatter",
      mode: "markers",
      name: "Expected",
      x: dates,
      y: expected,
      marker: {
        size: 8,
        color: chartColors.neutral,
        symbol: "circle-open",
      },
      hoverinfo: "skip",
    } as Data,
  ];

  const layout: Partial<Layout> = baseLayout({
    title: { text: "" },
    xaxis: { title: { text: "Date" } },
    yaxis: { title: { text: "Value" } },
    showlegend: true,
  });

  return (
    <ChartFrame title="Anomaly Timeline">
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
