import { ConfidenceGauge } from "../../charts";
import type { ConfidenceBreakdown } from "../types";

type Props = {
  score?: number;
  breakdown?: ConfidenceBreakdown;
  title?: string;
};

export function ConfidencePanel({ score, breakdown, title }: Props) {
  if (score == null) return null;

  const breakdownItems = breakdown
    ? [
        { label: "Data Quality", score: breakdown.data_quality },
        { label: "Analysis Depth", score: breakdown.analysis_depth },
        { label: "Actionability", score: breakdown.actionability },
      ]
    : undefined;

  return (
    <section className="analysis-section">
      <h3 className="analysis-section-title">{title ?? "Confidence"}</h3>
      <div className="confidence-panel">
        <ConfidenceGauge
          score={score}
          breakdown={breakdownItems}
          title={title ?? "Overall Confidence"}
        />
      </div>
    </section>
  );
}
