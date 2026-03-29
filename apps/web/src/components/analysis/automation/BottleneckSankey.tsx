import { SankeyDiagram } from "../../charts";
import type { SankeyNode, SankeyLink } from "../../charts";
import type { Bottleneck } from "../types";

type Props = {
  bottlenecks?: Bottleneck[];
};

function toSankey(bottlenecks: Bottleneck[]): {
  nodes: SankeyNode[];
  links: SankeyLink[];
} {
  const nodes: SankeyNode[] = [];
  const links: SankeyLink[] = [];

  const sourceId = "pipeline-input";
  nodes.push({ id: sourceId, label: "Pipeline Input" });

  bottlenecks.forEach((b) => {
    const stageId = `stage-${b.stage}`;
    nodes.push({ id: stageId, label: b.stage });

    links.push({ source: sourceId, target: stageId, value: b.time_pct });
  });

  const sinkId = "output";
  nodes.push({ id: sinkId, label: "Output" });

  bottlenecks.forEach((b) => {
    links.push({
      source: `stage-${b.stage}`,
      target: sinkId,
      value: b.cost_pct,
    });
  });

  return { nodes, links };
}

export function BottleneckSankey({ bottlenecks }: Props) {
  if (!bottlenecks || bottlenecks.length === 0) return null;

  const { nodes, links } = toSankey(bottlenecks);

  return (
    <SankeyDiagram
      nodes={nodes}
      links={links}
      title="Process Bottlenecks"
    />
  );
}
