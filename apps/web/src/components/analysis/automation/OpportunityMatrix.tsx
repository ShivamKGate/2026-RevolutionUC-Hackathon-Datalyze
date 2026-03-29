import { BubbleChart } from "../../charts";
import type { BubblePoint } from "../../charts";
import type { AutomationProcess } from "../types";

type Props = {
  processes?: AutomationProcess[];
};

const effortMap: Record<string, number> = {
  low: 1,
  medium: 2,
  high: 3,
  very_high: 4,
};

function effortToNumber(effort: string): number {
  return effortMap[effort.toLowerCase()] ?? 2;
}

function toPoints(processes: AutomationProcess[]): BubblePoint[] {
  const maxRoi = Math.max(...processes.map((p) => p.roi_months), 1);
  return processes.map((p) => ({
    x: effortToNumber(p.implementation_effort),
    y: p.impact_score,
    size: maxRoi / Math.max(p.roi_months, 0.1),
    label: p.name,
  }));
}

export function OpportunityMatrix({ processes }: Props) {
  if (!processes || processes.length === 0) return null;

  return (
    <BubbleChart
      points={toPoints(processes)}
      xLabel="Implementation Effort"
      yLabel="Impact Score"
      title="Automation Opportunity Matrix"
    />
  );
}
