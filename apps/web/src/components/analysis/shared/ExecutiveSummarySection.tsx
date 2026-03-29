import type { ExecutiveSummaryOutput } from "../types";

type Props = {
  data?: ExecutiveSummaryOutput;
};

export function ExecutiveSummarySection({ data }: Props) {
  if (!data) return null;

  return (
    <section className="executive-summary">
      <h2>{data.headline}</h2>
      <p className="executive-summary-overview">{data.situation_overview}</p>

      {data.key_findings?.length > 0 && (
        <>
          <p className="executive-summary-list-title">Key Findings</p>
          <ul>
            {data.key_findings.map((f, i) => (
              <li key={i}>{f}</li>
            ))}
          </ul>
        </>
      )}

      {data.risk_highlights?.length > 0 && (
        <>
          <p className="executive-summary-list-title">Risk Highlights</p>
          <ul>
            {data.risk_highlights.map((r, i) => (
              <li key={i}>{r}</li>
            ))}
          </ul>
        </>
      )}

      {data.next_actions?.length > 0 && (
        <>
          <p className="executive-summary-list-title">Next Actions</p>
          <ul>
            {data.next_actions.map((a, i) => (
              <li key={i}>{a}</li>
            ))}
          </ul>
        </>
      )}

      {data.confidence_statement && (
        <span className="executive-summary-confidence">
          {data.confidence_statement}
        </span>
      )}
    </section>
  );
}
