import { WaterfallChart } from "../../charts";
import type { WaterfallStep } from "../../charts";
import type { Driver } from "../types";

type Props = {
  drivers?: Driver[];
};

function driversToSteps(drivers: Driver[]): WaterfallStep[] {
  const steps: WaterfallStep[] = drivers.map((d) => ({
    label: d.factor,
    value: Math.abs(d.impact_pct),
    type: d.impact_pct >= 0 ? "increase" as const : "decrease" as const,
  }));

  const total = drivers.reduce((sum, d) => sum + d.impact_pct, 0);
  steps.push({ label: "Net Impact", value: total, type: "total" });
  return steps;
}

export function DriverWaterfall({ drivers }: Props) {
  if (!drivers || drivers.length === 0) return null;

  return (
    <WaterfallChart
      steps={driversToSteps(drivers)}
      title="Impact Drivers"
    />
  );
}
