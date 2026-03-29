import { useState } from "react";
import type { SOPDraft } from "../types";

type Props = {
  sopDraft?: SOPDraft;
};

function formatCurrency(n: number): string {
  if (Math.abs(n) >= 1_000_000) return `$${(n / 1_000_000).toFixed(2)}M`;
  if (Math.abs(n) >= 1_000) return `$${(n / 1_000).toFixed(1)}k`;
  return `$${n.toFixed(0)}`;
}

export function SOPPanel({ sopDraft }: Props) {
  const [checked, setChecked] = useState<Set<number>>(new Set());

  if (!sopDraft || !sopDraft.steps?.length) return null;

  function toggle(idx: number) {
    setChecked((prev) => {
      const next = new Set(prev);
      if (next.has(idx)) next.delete(idx);
      else next.add(idx);
      return next;
    });
  }

  return (
    <section className="analysis-section">
      <h3 className="analysis-section-title">Standard Operating Procedure</h3>
      <div className="sop-panel">
        <p className="sop-panel-savings">
          Estimated annual savings:{" "}
          {formatCurrency(sopDraft.estimated_savings_annual)}
        </p>
        {sopDraft.steps.map((step, i) => (
          <label
            key={i}
            className={`sop-step ${checked.has(i) ? "checked" : ""}`}
          >
            <input
              type="checkbox"
              checked={checked.has(i)}
              onChange={() => toggle(i)}
            />
            <span>{step}</span>
          </label>
        ))}
      </div>
    </section>
  );
}
