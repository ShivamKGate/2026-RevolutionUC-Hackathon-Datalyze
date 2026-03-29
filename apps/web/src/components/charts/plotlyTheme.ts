import type { Layout } from "plotly.js";

const BG = "#0f172a";
const PAPER = "#1e293b";
const TEXT = "#e8ecf1";
const MUTED = "#94a3b8";
const GRID = "rgba(51, 65, 85, 0.6)";
const ACCENT = "#3b82f6";

/** Base dark layout aligned with apps/web global CSS variables. */
export function baseLayout(partial: Partial<Layout> = {}): Partial<Layout> {
  return {
    paper_bgcolor: PAPER,
    plot_bgcolor: BG,
    font: { family: "Segoe UI, Tahoma, Geneva, Verdana, sans-serif", color: TEXT, size: 12 },
    title: { font: { color: TEXT, size: 14 } },
    xaxis: {
      gridcolor: GRID,
      zerolinecolor: GRID,
      tickfont: { color: MUTED },
      title: { font: { color: MUTED } },
    },
    yaxis: {
      gridcolor: GRID,
      zerolinecolor: GRID,
      tickfont: { color: MUTED },
      title: { font: { color: MUTED } },
    },
    margin: { l: 56, r: 24, t: 48, b: 56 },
    autosize: true,
    showlegend: true,
    legend: {
      font: { color: MUTED },
      bgcolor: "rgba(15, 23, 42, 0.5)",
      bordercolor: GRID,
      borderwidth: 1,
    },
    ...partial,
  };
}

export const chartColors = {
  accent: ACCENT,
  positive: "#22c55e",
  negative: "#ef4444",
  neutral: "#64748b",
  series: ["#3b82f6", "#a855f7", "#14b8a6", "#f59e0b", "#ec4899"],
};
