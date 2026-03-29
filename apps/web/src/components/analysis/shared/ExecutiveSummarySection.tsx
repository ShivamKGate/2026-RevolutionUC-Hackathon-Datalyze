import { unknownToDisplayText } from "../../../lib/renderSafe";
import type { ExecutiveSummaryOutput } from "../types";

type Props = {
  data?: ExecutiveSummaryOutput;
};

export function ExecutiveSummarySection({ data }: Props) {
  if (!data) return null;

  return (
    <section className="executive-summary">
      <h2>{unknownToDisplayText(data.headline as unknown)}</h2>
      <p className="executive-summary-overview">
        {unknownToDisplayText(data.situation_overview as unknown)}
      </p>

      {data.key_findings?.length > 0 && (
        <>
          <p className="executive-summary-list-title">Key Findings</p>
          <ul>
            {data.key_findings.map((f, i) => (
              <li key={i}>{unknownToDisplayText(f as unknown)}</li>
            ))}
          </ul>
        </>
      )}

      {data.risk_highlights?.length > 0 && (
        <>
          <p className="executive-summary-list-title">Risk Highlights</p>
          <ul>
            {data.risk_highlights.map((r, i) => (
              <li key={i}>{unknownToDisplayText(r as unknown)}</li>
            ))}
          </ul>
        </>
      )}

      {data.next_actions?.length > 0 && (
        <>
          <p className="executive-summary-list-title">Next Actions</p>
          <ul>
            {data.next_actions.map((a, i) => (
              <li key={i}>{unknownToDisplayText(a as unknown)}</li>
            ))}
          </ul>
        </>
      )}

      {(() => {
        const conf = unknownToDisplayText(
          data.confidence_statement as unknown,
        ).trim();
        return conf ? (
          <span className="executive-summary-confidence">{conf}</span>
        ) : null;
      })()}
    </section>
  );
}
