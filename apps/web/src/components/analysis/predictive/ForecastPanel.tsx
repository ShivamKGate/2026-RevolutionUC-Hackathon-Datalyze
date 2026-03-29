import { TimeSeriesChart } from "../../charts";
import type { TimeSeriesPoint } from "../../charts";
import type { ForecastMetric } from "../types";

type Props = {
  forecasts?: ForecastMetric[];
};

function combineSeries(f: ForecastMetric): TimeSeriesPoint[] {
  const hist: TimeSeriesPoint[] = (f.historical ?? []).map((p) => ({
    date: p.date,
    value: p.value,
  }));
  const pred: TimeSeriesPoint[] = (f.predicted ?? []).map((p) => ({
    date: p.date,
    value: p.value,
    lower: p.lower,
    upper: p.upper,
  }));
  return [...hist, ...pred];
}

export function ForecastPanel({ forecasts }: Props) {
  if (!forecasts || forecasts.length === 0) return null;

  return (
    <section className="analysis-section">
      <h3 className="analysis-section-title">Forecasts</h3>
      {forecasts.map((f) => (
        <TimeSeriesChart
          key={f.metric}
          series={combineSeries(f)}
          title={`${f.metric} (${f.trend_direction})`}
          showConfidenceBands
        />
      ))}
    </section>
  );
}
