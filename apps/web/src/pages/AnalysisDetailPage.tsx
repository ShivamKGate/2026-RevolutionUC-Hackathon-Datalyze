import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import {
  getPipelineRun,
  getPipelineRunLogs,
  type PipelineRun,
  type PipelineRunLog,
} from "../lib/api";

export default function AnalysisDetailPage() {
  const { slug } = useParams<{ slug: string }>();
  const [run, setRun] = useState<PipelineRun | null>(null);
  const [logs, setLogs] = useState<PipelineRunLog[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    if (!slug) return;
    let cancelled = false;
    let intervalId: number | undefined;

    const load = async () => {
      try {
        const [r, logRows] = await Promise.all([
          getPipelineRun(slug),
          getPipelineRunLogs(slug),
        ]);
        if (cancelled) return;
        setRun(r);
        setLogs(logRows);
        setError(null);
        if (r.status === "pending" || r.status === "running") {
          if (intervalId == null) {
            intervalId = window.setInterval(() => {
              void load();
            }, 2500);
          }
        } else if (intervalId != null) {
          window.clearInterval(intervalId);
          intervalId = undefined;
        }
      } catch (e) {
        if (!cancelled) {
          setError(e instanceof Error ? e.message : "Failed to load run");
        }
      }
    };

    void load();

    return () => {
      cancelled = true;
      if (intervalId != null) {
        window.clearInterval(intervalId);
      }
    };
  }, [slug]);

  async function copyShareLink() {
    try {
      await navigator.clipboard.writeText(window.location.href);
      setCopied(true);
      window.setTimeout(() => setCopied(false), 1500);
    } catch {
      setCopied(false);
    }
  }

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
        {run.track ? ` · ${run.track}` : ""}
      </p>
      <div style={{ display: "flex", gap: "0.5rem", flexWrap: "wrap" }}>
        <button
          type="button"
          className="btn-secondary"
          onClick={() => void copyShareLink()}
        >
          Copy share link
        </button>
        {copied && (
          <span
            style={{
              color: "#4ade80",
              alignSelf: "center",
              fontSize: "0.875rem",
            }}
          >
            Link copied
          </span>
        )}
      </div>
      {run.summary && <div className="analysis-summary">{run.summary}</div>}
      {run.config_json && Object.keys(run.config_json).length > 0 && (
        <section style={{ marginTop: "1.25rem" }}>
          <h2 className="section-title">Runtime config</h2>
          <pre className="pipeline-log-block">
            {JSON.stringify(run.config_json, null, 2)}
          </pre>
        </section>
      )}
      <section style={{ marginTop: "1.5rem" }}>
        <h2 className="section-title">Pipeline log</h2>
        <pre className="pipeline-log-block">
          {logs.length > 0
            ? logs
                .map(
                  (entry) =>
                    `[${entry.timestamp ?? "n/a"}] [${entry.stage}] [${entry.agent}] ${entry.action}: ${entry.detail}`,
                )
                .join("\n")
            : run.pipeline_log.join("\n")}
        </pre>
      </section>
      <section style={{ marginTop: "1.5rem" }}>
        <h2 className="section-title">Agent activity</h2>
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
      {run.run_dir_path && (
        <p
          style={{
            marginTop: "1rem",
            color: "var(--text-muted)",
            fontSize: "0.85rem",
          }}
        >
          Run artifacts: <code className="inline-code">{run.run_dir_path}</code>
        </p>
      )}
    </div>
  );
}
