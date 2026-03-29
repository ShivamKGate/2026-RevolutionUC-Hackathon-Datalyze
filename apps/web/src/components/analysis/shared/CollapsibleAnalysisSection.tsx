import { type ReactNode, useEffect, useState } from "react";

type Props = {
  title: string;
  summary?: ReactNode;
  defaultOpen?: boolean;
  storageKey?: string;
  children: ReactNode;
};

export function CollapsibleAnalysisSection({
  title,
  summary,
  defaultOpen = false,
  storageKey,
  children,
}: Props) {
  const [open, setOpen] = useState(() => {
    if (storageKey) {
      const saved = sessionStorage.getItem(storageKey);
      if (saved !== null) return saved === "true";
    }
    return defaultOpen;
  });

  useEffect(() => {
    if (storageKey) {
      sessionStorage.setItem(storageKey, String(open));
    }
  }, [open, storageKey]);

  return (
    <section className="collapsible-section">
      <button
        type="button"
        className="collapsible-section-header"
        aria-expanded={open}
        onClick={() => setOpen((o) => !o)}
      >
        <span className="collapsible-section-title">{title}</span>
        {!open && summary && (
          <span className="collapsible-section-summary">{summary}</span>
        )}
        <span className="collapsible-section-chevron" aria-hidden="true">
          {open ? "▾" : "▸"}
        </span>
      </button>
      {open && (
        <div className="collapsible-section-body">
          {children}
        </div>
      )}
    </section>
  );
}
