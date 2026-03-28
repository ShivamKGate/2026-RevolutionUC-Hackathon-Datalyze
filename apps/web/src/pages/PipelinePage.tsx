import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { listPipelineRuns, type PipelineRun } from "../lib/api";

export default function PipelinePage() {
  const [runs, setRuns] = useState<PipelineRun[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      setRuns(await listPipelineRuns());
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load pipeline runs");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  const latest = runs[0];

  return (
    <div>
      <h1 style={{ marginTop: 0 }}>Pipeline status</h1>
      {error && (
        <div
          className="status error"
          style={{
            marginBottom: "1rem",
            padding: "0.6rem 0.75rem",
            borderRadius: 6,
          }}
        >
          {error}
        </div>
      )}
      {loading ? (
        <div className="spinner-page" style={{ minHeight: 120 }}>
          <div className="spinner" />
        </div>
      ) : !latest ? (
        <div className="empty-state">
          <p>No pipeline runs yet.</p>
          <p style={{ fontSize: "0.875rem", color: "var(--text-muted)" }}>
            Start an analysis from the dashboard — placeholder logs will appear
            here.
          </p>
          <Link
            to="/dashboard"
            className="btn-primary"
            style={{ marginTop: "0.75rem", display: "inline-block" }}
          >
            Go to dashboard
          </Link>
        </div>
      ) : (
        <>
          <div className="pipeline-latest-banner">
            <div>
              <strong>Latest run</strong>{" "}
              <Link
                to={`/analysis/${latest.slug}`}
                className="analysis-run-link"
              >
                {latest.slug}
              </Link>
            </div>
            <span
              className={`pipeline-status-pill pipeline-status-${latest.status}`}
            >
              {latest.status}
            </span>
          </div>
          <p style={{ color: "var(--text-muted)", fontSize: "0.9rem" }}>
            Started {latest.started_at}
            {latest.ended_at ? ` · Ended ${latest.ended_at}` : ""}
          </p>
          {latest.summary && (
            <p className="analysis-summary">{latest.summary}</p>
          )}
          <h2 className="section-title">Log (placeholder)</h2>
          <pre className="pipeline-log-block">
            {latest.pipeline_log.join("\n")}
          </pre>
        </>
      )}
    </div>
  );
}
