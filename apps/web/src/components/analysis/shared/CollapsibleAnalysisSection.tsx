import { useEffect, useId, useState, type ReactNode } from "react";

type Props = {
  title: string;
  defaultOpen?: boolean;
  summary: ReactNode;
  children: ReactNode;
  /** sessionStorage key for open state (per run slug prefix from parent). */
  storageKey?: string;
  className?: string;
};

export function CollapsibleAnalysisSection({
  title,
  defaultOpen = false,
  summary,
  children,
  storageKey,
  className,
}: Props) {
  const panelId = useId();
  const [open, setOpen] = useState(() => {
    if (storageKey && typeof sessionStorage !== "undefined") {
      const v = sessionStorage.getItem(storageKey);
      if (v === "1") return true;
      if (v === "0") return false;
    }
    return defaultOpen;
  });

  useEffect(() => {
    if (!storageKey || typeof sessionStorage === "undefined") return;
    sessionStorage.setItem(storageKey, open ? "1" : "0");
  }, [open, storageKey]);

  return (
    <section
      className={`collapsible-analysis-section ${className ?? ""}`.trim()}
    >
      <button
        type="button"
        className="collapsible-analysis-toggle"
        aria-expanded={open}
        aria-controls={panelId}
        onClick={() => setOpen((o) => !o)}
      >
        <span className="collapsible-analysis-chevron" aria-hidden>
          {open ? "▼" : "▶"}
        </span>
        <span className="collapsible-analysis-title">{title}</span>
        {!open && (
          <span className="collapsible-analysis-summary">{summary}</span>
        )}
      </button>
      {open ? (
        <div id={panelId} className="collapsible-analysis-body">
          {children}
        </div>
      ) : (
        <div id={panelId} className="collapsible-analysis-body" hidden />
      )}
    </section>
  );
}
