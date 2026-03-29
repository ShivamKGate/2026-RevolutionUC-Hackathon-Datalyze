import type { AutomationProcess } from "../types";

type Props = {
  processes?: AutomationProcess[];
};

function formatCurrency(n: number): string {
  if (Math.abs(n) >= 1_000_000) return `$${(n / 1_000_000).toFixed(2)}M`;
  if (Math.abs(n) >= 1_000) return `$${(n / 1_000).toFixed(1)}k`;
  return `$${n.toFixed(0)}`;
}

export function StrategicPriorities({ processes }: Props) {
  if (!processes || processes.length === 0) return null;

  const sorted = [...processes].sort(
    (a, b) => b.impact_score - a.impact_score,
  );

  return (
    <section className="analysis-section">
      <h3 className="analysis-section-title">Strategic Priorities</h3>
      <div className="strategic-priorities">
        {sorted.map((p) => (
          <div key={p.name} className="strategic-card">
            <h4 className="strategic-card-name">{p.name}</h4>
            <div className="strategic-card-row">
              <span>Current</span>
              <strong>
                {p.current_time_hours}h / {formatCurrency(p.cost_current)}
              </strong>
            </div>
            <div className="strategic-card-row">
              <span>Automated</span>
              <strong>
                {p.automated_time_hours}h / {formatCurrency(p.cost_automated)}
              </strong>
            </div>
            <div className="strategic-card-row">
              <span>ROI timeline</span>
              <strong>{p.roi_months} months</strong>
            </div>
            <p className="strategic-card-savings">
              Save {formatCurrency(p.cost_current - p.cost_automated)}/cycle &middot;{" "}
              {(p.current_time_hours - p.automated_time_hours).toFixed(1)}h freed
            </p>
          </div>
        ))}
      </div>
    </section>
  );
}
