import Plot from "react-plotly.js";
import type { Data, Layout } from "plotly.js";
import { ChartFrame } from "./ChartFrame";
import { baseLayout } from "./plotlyTheme";

export type ConfidenceGaugeProps = {
  score: number;
  breakdown?: { label: string; score: number }[];
  title?: string;
  className?: string;
};

export function ConfidenceGauge({
  score,
  breakdown,
  title = "Confidence",
  className,
}: ConfidenceGaugeProps) {
  const pct = Math.min(100, Math.max(0, score <= 1 ? score * 100 : score));

  const data: Data[] = [
    {
      type: "indicator",
      mode: "gauge+number",
      value: pct,
      number: { suffix: "%", font: { color: "#e8ecf1" } },
      gauge: {
        axis: { range: [0, 100], tickcolor: "#64748b" },
        bar: { color: "#3b82f6" },
        bgcolor: "#0f172a",
        borderwidth: 1,
        bordercolor: "#334155",
        steps: [
          { range: [0, 40], color: "rgba(239, 68, 68, 0.35)" },
          { range: [40, 70], color: "rgba(245, 158, 11, 0.35)" },
          { range: [70, 100], color: "rgba(34, 197, 94, 0.35)" },
        ],
      },
    },
  ];

  const layout: Partial<Layout> = baseLayout({
    title: { text: "" },
    margin: { t: 24, r: 24, b: 24, l: 24 },
    height: 280,
  });

  return (
    <div className={`confidence-gauge-wrap ${className ?? ""}`.trim()}>
      <ChartFrame title={title}>
        <div className="plotly-chart-host" style={{ minHeight: 260 }}>
          <Plot
            data={data}
            layout={layout}
            style={{ width: "100%", height: 260 }}
            useResizeHandler
            config={{ displayModeBar: false, responsive: true }}
          />
        </div>
      </ChartFrame>
      {breakdown && breakdown.length > 0 && (
        <ul className="confidence-gauge-breakdown">
          {breakdown.map((row) => (
            <li key={row.label} className="confidence-gauge-row">
              <span>{row.label}</span>
              <span>
                {(row.score <= 1 ? row.score * 100 : row.score).toFixed(0)}%
              </span>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
