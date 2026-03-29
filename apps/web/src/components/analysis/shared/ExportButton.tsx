import { useState } from "react";

type Props = {
  slug: string;
};

export function ExportButton({ slug }: Props) {
  const [loading, setLoading] = useState(false);

  async function handleExport() {
    setLoading(true);
    try {
      const res = await fetch(`/api/v1/runs/${encodeURIComponent(slug)}/export/pdf`);
      if (!res.ok) throw new Error(`Export failed (${res.status})`);

      const blob = await res.blob();
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
      setLoading(false);
    }
  }

  return (
    <button
      className="export-button"
      onClick={handleExport}
      disabled={loading}
    >
      {loading ? "Generating…" : "Export PDF"}
    </button>
  );
}
