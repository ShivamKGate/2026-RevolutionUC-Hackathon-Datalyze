import "./charts.css";
import { unknownToDisplayText } from "../../lib/renderSafe";

export type RecommendationCardProps = {
  action: string;
  priority: "high" | "medium" | "low";
  impact: string;
  confidence: number;
  source_agent: string;
  className?: string;
};

function priorityClass(p: RecommendationCardProps["priority"]): string {
  switch (p) {
    case "high":
      return "recommendation-card-priority--high";
    case "medium":
      return "recommendation-card-priority--medium";
    default:
      return "recommendation-card-priority--low";
  }
}

export function RecommendationCard({
  action,
  priority,
  impact,
  confidence,
  source_agent,
  className = "",
}: RecommendationCardProps) {
  const actionText = unknownToDisplayText(action as unknown);
  const impactText = unknownToDisplayText(impact as unknown);
  const confNum =
    typeof confidence === "number" && Number.isFinite(confidence)
      ? confidence
      : 0;
  const confPct = (confNum <= 1 ? confNum * 100 : confNum).toFixed(0);

  return (
    <article className={`recommendation-card ${className}`.trim()}>
      <div className="recommendation-card-header">
        <h4 className="recommendation-card-action">{actionText}</h4>
        <span
          className={`recommendation-card-priority ${priorityClass(priority)}`}
        >
          {priority}
        </span>
      </div>
      <p className="recommendation-card-impact">{impactText}</p>
      <div className="recommendation-card-footer">
        <span>{confPct}% confidence</span>
        <span className="recommendation-card-source">{source_agent}</span>
      </div>
    </article>
  );
}
