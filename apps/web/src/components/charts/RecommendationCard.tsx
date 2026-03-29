import "./charts.css";

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
  const confPct = (confidence <= 1 ? confidence * 100 : confidence).toFixed(0);

  return (
    <article className={`recommendation-card ${className}`.trim()}>
      <div className="recommendation-card-header">
        <h4 className="recommendation-card-action">{action}</h4>
        <span
          className={`recommendation-card-priority ${priorityClass(priority)}`}
        >
          {priority}
        </span>
      </div>
      <p className="recommendation-card-impact">{impact}</p>
      <div className="recommendation-card-footer">
        <span>{confPct}% confidence</span>
        <span className="recommendation-card-source">{source_agent}</span>
      </div>
    </article>
  );
}
