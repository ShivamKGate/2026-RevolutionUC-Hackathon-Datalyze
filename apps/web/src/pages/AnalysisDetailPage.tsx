import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { getPipelineRun, type PipelineRun } from "../lib/api";

export default function AnalysisDetailPage() {
  const { slug } = useParams<{ slug: string }>();
  const [run, setRun] = useState<PipelineRun | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!slug) return;
    let cancelled = false;
    getPipelineRun(slug)
      .then((r) => {
        if (!cancelled) setRun(r);
      })
      .catch((e) => {
        if (!cancelled)
          setError(e instanceof Error ? e.message : "Failed to load run");
      });
    return () => {
      cancelled = true;
    };
  }, [slug]);

  if (error) {
    return (
      <div>
        <p className="status error">{error}</p>
        <Link to="/dashboard">Back to dashboard</Link>
      </div>
    );
  }

  if (!run) {
    return (
      <div className="spinner-page">
        <div className="spinner" />
      </div>
    );
  }

  return (
    <div>
      <div style={{ marginBottom: "1.25rem" }}>
        <Link
          to="/dashboard"
          className="nav-btn nav-btn-ghost"
          style={{ display: "inline-block" }}
        >
          ← Dashboard
        </Link>
      </div>
      <h1 style={{ marginTop: 0 }}>Analysis</h1>
      <p style={{ color: "var(--text-muted)", marginTop: "-0.5rem" }}>
        Run <code className="inline-code">{run.slug}</code> · {run.status}
      </p>
      {run.summary && <div className="analysis-summary">{run.summary}</div>}
      <section style={{ marginTop: "1.5rem" }}>
        <h2 className="section-title">Pipeline log</h2>
        <pre className="pipeline-log-block">{run.pipeline_log.join("\n")}</pre>
      </section>
      <section style={{ marginTop: "1.5rem" }}>
        <h2 className="section-title">Agent activity (placeholder)</h2>
        <ul className="agent-activity-list">
          {run.agent_activity.map((a) => (
            <li
              key={`${run.slug}-${a.agent_id}`}
              className="agent-activity-item"
            >
              <strong>{a.agent_name}</strong>
              <span className="agent-activity-status">{a.status}</span>
              <p className="agent-activity-msg">{a.message}</p>
            </li>
          ))}
        </ul>
      </section>
    </div>
  );
}
