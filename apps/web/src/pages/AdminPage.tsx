import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { getAdminReplayList, type DemoReplayListEntry } from "../lib/api";

export default function AdminPage() {
  const [rows, setRows] = useState<DemoReplayListEntry[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      setRows(await getAdminReplayList());
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load replays");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  return (
    <div>
      <h1 style={{ marginTop: 0 }}>Admin panel</h1>
      <p style={{ color: "var(--text-muted)" }}>
        Demo replay snapshots (latest successful run per track for your
        company).
      </p>

      {error && (
        <div className="status error" style={{ marginBottom: "1rem" }}>
          {error}
        </div>
      )}

      <section style={{ marginTop: "1.5rem" }}>
        <h2 className="section-title">Demo replay</h2>
        {loading ? (
          <div className="spinner-page" style={{ minHeight: 100 }}>
            <div className="spinner" />
          </div>
        ) : rows.length === 0 ? (
          <p style={{ color: "var(--text-muted)" }}>
            No replays captured yet. Complete an analysis run successfully to
            populate this list.
          </p>
        ) : (
          <ul className="analysis-run-list">
            {rows.map((r) => (
              <li key={r.track} className="analysis-run-card">
                <div>
                  <strong style={{ textTransform: "capitalize" }}>
                    {r.track.replace("_", " ")}
                  </strong>
                  <p className="analysis-run-meta">
                    Captured {r.captured_at ?? "—"} · Run{" "}
                    <code className="inline-code">{r.source_slug}</code>
                  </p>
                  {r.run_summary && (
                    <p className="analysis-run-summary">
                      {r.run_summary.slice(0, 160)}
                    </p>
                  )}
                </div>
                <Link
                  to={`/analysis/${r.source_slug}`}
                  className="btn-primary"
                  style={{ alignSelf: "center" }}
                >
                  Open analysis
                </Link>
              </li>
            ))}
          </ul>
        )}
      </section>
    </div>
  );
}
