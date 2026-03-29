import { BarChart } from "../../charts";
import type { AutomationProcess } from "../types";

type Props = {
  processes?: AutomationProcess[];
};

function buildProjection(processes: AutomationProcess[]) {
  const totalHoursSaved = processes.reduce(
    (sum, p) => sum + (p.current_time_hours - p.automated_time_hours),
    0,
  );

  const hoursPerFteMonth = 160;
  const months = ["Month 1", "Month 2", "Month 3", "Month 4", "Month 5", "Month 6"];

  const values = months.map((_, i) => {
    const ramp = Math.min(1, (i + 1) / 3);
    return parseFloat(((totalHoursSaved * ramp) / hoursPerFteMonth).toFixed(2));
  });

  return { months, values };
}

export function CapacityForecast({ processes }: Props) {
  if (!processes || processes.length === 0) return null;

  const { months, values } = buildProjection(processes);

  return (
    <BarChart
      categories={months}
      values={values}
      title="Capacity Release Projection (FTE Equivalent)"
    />
  );
}
