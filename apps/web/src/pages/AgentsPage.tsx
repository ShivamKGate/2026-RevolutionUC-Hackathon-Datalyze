import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { getLatestPipelineRun, type AgentActivityRow } from "../lib/api";

export default function AgentsPage() {
  const [rows, setRows] = useState<AgentActivityRow[]>([]);
  const [slug, setSlug] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    getLatestPipelineRun()
      .then((run) => {
        if (cancelled) return;
        if (run) {
          setRows(run.agent_activity ?? []);
          setSlug(run.slug);
        } else {
          setRows([]);
          setSlug(null);
        }
      })
      .catch(() => {
        if (!cancelled) {
          setRows([]);
          setSlug(null);
        }
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <div>
      <h1 style={{ marginTop: 0 }}>Agent activity</h1>
      {loading ? (
        <div className="spinner-page" style={{ minHeight: 120 }}>
          <div className="spinner" />
        </div>
      ) : !rows.length ? (
        <div className="empty-state">
          <p>No agent activity yet.</p>
          <p style={{ fontSize: "0.875rem", color: "var(--text-muted)" }}>
            Run an analysis from the dashboard — placeholder rows mirror the
            live agent registry (read-only).
          </p>
          <Link
            to="/dashboard"
            className="btn-primary"
            style={{ marginTop: "0.75rem", display: "inline-block" }}
          >
            Dashboard
          </Link>
        </div>
      ) : (
        <>
          {slug && (
            <p style={{ color: "var(--text-muted)", marginBottom: "1rem" }}>
              From latest run{" "}
              <Link to={`/analysis/${slug}`} className="analysis-run-link">
                {slug}
              </Link>
            </p>
          )}
          <ul className="agent-activity-list">
            {rows.map((a) => (
              <li key={a.agent_id} className="agent-activity-item">
                <strong>{a.agent_name}</strong>
                <span className="agent-activity-status">{a.status}</span>
                <p className="agent-activity-msg">{a.message}</p>
              </li>
            ))}
          </ul>
        </>
      )}
    </div>
  );
}
