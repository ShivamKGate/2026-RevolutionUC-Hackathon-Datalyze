import { TimeSeriesChart } from "../../charts";
import type { TimeSeriesPoint } from "../../charts";
import type { ForecastMetric } from "../types";

type Props = {
  segments?: ForecastMetric[];
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

export function SegmentForecasts({ segments }: Props) {
  if (!segments || segments.length === 0) return null;

  return (
    <section className="analysis-section">
      <h3 className="analysis-section-title">Segment Forecasts</h3>
      <div className="segment-forecasts-grid">
        {segments.map((seg) => (
          <TimeSeriesChart
            key={seg.metric}
            series={combineSeries(seg)}
            title={seg.metric}
            showConfidenceBands
          />
        ))}
      </div>
    </section>
  );
}
