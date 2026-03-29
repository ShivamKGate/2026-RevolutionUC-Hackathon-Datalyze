import { BubbleChart } from "../../charts";
import type { BubblePoint } from "../../charts";
import type { AutomationProcess } from "../types";

type Props = {
  processes?: AutomationProcess[];
};

function toPoints(processes: AutomationProcess[]): BubblePoint[] {
  return processes.map((p) => ({
    x: p.current_time_hours - p.automated_time_hours,
    y: p.cost_current - p.cost_automated,
    size: p.roi_months,
    label: p.name,
  }));
}

export function ROIBubbles({ processes }: Props) {
  if (!processes || processes.length === 0) return null;

  return (
    <BubbleChart
      points={toPoints(processes)}
      xLabel="Hours Saved"
      yLabel="Cost Saved"
      title="ROI Analysis"
    />
  );
}
