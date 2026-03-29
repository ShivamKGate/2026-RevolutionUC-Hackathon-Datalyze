import { RecommendationCard } from "../../charts";
import type { RecommendationCardProps } from "../../charts";

type Props = {
  recommendations?: RecommendationCardProps[];
};

export function RecommendationsPanel({ recommendations }: Props) {
  if (!recommendations || recommendations.length === 0) return null;

  return (
    <section className="analysis-section">
      <h3 className="analysis-section-title">Recommendations</h3>
      <div className="recommendations-panel">
        {recommendations.map((rec, i) => (
          <RecommendationCard key={i} {...rec} />
        ))}
      </div>
    </section>
  );
}
