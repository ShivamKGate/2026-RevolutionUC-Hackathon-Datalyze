import Plot from "react-plotly.js";
import type { Data, Layout } from "plotly.js";
import { ChartFrame } from "./ChartFrame";
import { baseLayout } from "./plotlyTheme";
import type { SankeyLink, SankeyNode } from "./types";

export type SankeyDiagramProps = {
  nodes: SankeyNode[];
  links: SankeyLink[];
  title: string;
  className?: string;
};

export function SankeyDiagram({ nodes, links, title, className }: SankeyDiagramProps) {
  const idToIndex = new Map(nodes.map((n, i) => [n.id, i]));
  const label = nodes.map((n) => n.label);
  const source = links.map((l) => idToIndex.get(l.source) ?? 0);
  const target = links.map((l) => idToIndex.get(l.target) ?? 0);
  const value = links.map((l) => l.value);

  const data: Data[] = [
    {
      type: "sankey",
      orientation: "h",
      node: {
        pad: 12,
        thickness: 14,
        line: { color: "rgba(148, 163, 184, 0.35)", width: 0.5 },
        label,
        color: label.map(() => "#334155"),
      },
      link: {
        source,
        target,
        value,
        color: "rgba(59, 130, 246, 0.35)",
      },
    },
  ];

  const layout: Partial<Layout> = baseLayout({
    title: { text: "" },
    showlegend: false,
  });

  return (
    <ChartFrame title={title} className={className}>
      <div className="plotly-chart-host">
        <Plot
          data={data}
          layout={layout}
          style={{ width: "100%", height: 420 }}
          useResizeHandler
          config={{ displayModeBar: true, responsive: true }}
        />
      </div>
    </ChartFrame>
  );
}
