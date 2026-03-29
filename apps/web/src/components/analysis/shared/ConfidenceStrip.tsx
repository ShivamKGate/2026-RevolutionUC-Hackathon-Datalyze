import { useState, type CSSProperties, type KeyboardEvent } from "react";
import { coerceConfidenceScore } from "../../../lib/renderSafe";
import type { ConfidenceBreakdown } from "../types";

type Props = {
  /** May be a number or API shape `{ overall_confidence, basis }` */
  score?: unknown;
  breakdown?: ConfidenceBreakdown;
  /** `header`: compact top-of-page card; whole card toggles breakdown beside the ring. */
  variant?: "default" | "header";
};

export function ConfidenceStrip({
  score,
  breakdown,
  variant = "default",
}: Props) {
  const [expanded, setExpanded] = useState(false);
  const n = coerceConfidenceScore(score);
  if (n == null) return null;

  const pct = Math.min(
    100,
    Math.max(0, Math.round((n <= 1 ? n : n / 100) * 100)),
  );

  const rootClass =
    variant === "header"
      ? "confidence-strip confidence-strip--header-card"
      : "confidence-strip";

  const interactive = Boolean(breakdown) || variant === "header";

  const rootClassNames = [
    rootClass,
    expanded ? "confidence-strip--expanded" : "",
    interactive ? "confidence-strip--interactive" : "",
  ]
    .filter(Boolean)
    .join(" ");

  function toggle() {
    if (!interactive) return;
    setExpanded((v) => !v);
  }

  function onKeyDown(e: KeyboardEvent) {
    if (!interactive) return;
    if (e.key === "Enter" || e.key === " ") {
      e.preventDefault();
      setExpanded((v) => !v);
    }
  }

  return (
    <div
      className={rootClassNames}
      onClick={interactive ? toggle : undefined}
      onKeyDown={interactive ? onKeyDown : undefined}
      role={interactive ? "button" : undefined}
      tabIndex={interactive ? 0 : undefined}
      aria-expanded={interactive ? expanded : undefined}
      aria-label={
        interactive
          ? expanded
            ? "Confidence breakdown expanded; press to collapse"
            : "Confidence; press to show breakdown"
          : undefined
      }
    >
      <div className="confidence-strip-row">
        <span className="confidence-strip-label">Confidence</span>
        <div
          className="confidence-strip-ring"
          style={{ "--conf-pct": String(pct) } as CSSProperties}
          title={`${pct}%`}
        >
          <div className="confidence-strip-ring-inner">
            <span className="confidence-strip-pct">{pct}%</span>
          </div>
        </div>
      </div>
      {expanded && breakdown && (
        <ul className="confidence-strip-breakdown confidence-strip-breakdown--side">
          <li>
            <span>Data quality</span>
            <span>{Math.round(breakdown.data_quality * 100)}%</span>
          </li>
          <li>
            <span>Analysis depth</span>
            <span>{Math.round(breakdown.analysis_depth * 100)}%</span>
          </li>
          <li>
            <span>Actionability</span>
            <span>{Math.round(breakdown.actionability * 100)}%</span>
          </li>
        </ul>
      )}
      {expanded && !breakdown && variant === "header" && (
        <p className="confidence-strip-breakdown-note confidence-strip-breakdown-note--side">
          Breakdown appears when the evaluator returns confidence_breakdown for
          this run.
        </p>
      )}
    </div>
  );
}
