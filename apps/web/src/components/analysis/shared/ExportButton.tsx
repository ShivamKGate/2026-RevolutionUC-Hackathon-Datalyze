import { useState } from "react";

import { exportRunHTML, exportRunPDF } from "../../../lib/api";

type Props = {
  slug: string;
};

export function ExportButton({ slug }: Props) {
  const [loading, setLoading] = useState<"html" | "pdf" | null>(null);

  async function downloadHtml() {
    setLoading("html");
    try {
      const blob = await exportRunHTML(slug);
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `${slug}-report.html`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      URL.revokeObjectURL(url);
    } catch {
      console.error("HTML export failed");
    } finally {
      setLoading(null);
    }
  }

  async function downloadPdf() {
    setLoading("pdf");
    try {
      const blob = await exportRunPDF(slug);
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `${slug}-report.pdf`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      URL.revokeObjectURL(url);
    } catch {
      console.error("PDF export failed");
    } finally {
      setLoading(null);
    }
  }

  const busy = loading !== null;

  return (
    <div className="export-actions">
      <button
        type="button"
        className="export-button export-button-primary"
        onClick={() => void downloadHtml()}
        disabled={busy}
        title="Charts and full insight text; open the file, then Print → Save as PDF"
      >
        {loading === "html" ? "Generating…" : "Export HTML report"}
      </button>
      <button
        type="button"
        className="export-button"
        onClick={() => void downloadPdf()}
        disabled={busy}
        title="PDF with charts as images and knowledge-graph node table"
      >
        {loading === "pdf" ? "Generating…" : "Export summary PDF"}
      </button>
    </div>
  );
}
