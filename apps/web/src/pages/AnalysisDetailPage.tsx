import { useEffect, useMemo, useState, type ReactNode } from "react";
import { Link, useParams } from "react-router-dom";
import {
  getPipelineRun,
  getPipelineRunLogs,
  type PipelineRun,
  type PipelineRunLog,
} from "../lib/api";
import { TrackRenderer } from "../components/analysis";
import type {
  AgentResults,
  VisualizationPlan,
} from "../components/analysis/types";
import { KnowledgeGraphViewer } from "../components/knowledge-graph/KnowledgeGraphViewer";

function extractAgentResults(run: PipelineRun): AgentResults {
  const rp = run.replay_payload;
  if (
    rp &&
    typeof rp === "object" &&
    "agent_results" in rp &&
    rp.agent_results
  ) {
    return rp.agent_results as AgentResults;
  }
  return {};
}

function extractVisualizationPlan(
  run: PipelineRun,
): VisualizationPlan | undefined {
  const rp = run.replay_payload;
  if (!rp || typeof rp !== "object") return undefined;
  if ("visualization_plan" in rp && rp.visualization_plan) {
    return rp.visualization_plan as VisualizationPlan;
  }
  const ar = extractAgentResults(run);
  if (ar.output_evaluator) return ar.output_evaluator;
  return undefined;
}

function Collapsible({
  title,
  defaultOpen,
  children,
}: {
  title: string;
  defaultOpen?: boolean;
  children: ReactNode;
}) {
  const [open, setOpen] = useState(defaultOpen ?? false);
  return (
    <section style={{ marginTop: "1.25rem" }}>
      <button
        type="button"
        onClick={() => setOpen((o) => !o)}
        className="nav-btn nav-btn-ghost"
        style={{ width: "100%", textAlign: "left", marginBottom: "0.5rem" }}
      >
        {open ? "▼" : "▶"} {title}
      </button>
      {open && children}
    </section>
  );
}

export default function AnalysisDetailPage() {
  const { slug } = useParams<{ slug: string }>();
  const [run, setRun] = useState<PipelineRun | null>(null);
  const [logs, setLogs] = useState<PipelineRunLog[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);
  const [tab, setTab] = useState<"analysis" | "graph">("analysis");

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

  const agentResults = useMemo(
    () => (run ? extractAgentResults(run) : {}),
    [run],
  );
  const vizPlan = useMemo(
    () => (run ? extractVisualizationPlan(run) : undefined),
    [run],
  );
  const kg = agentResults.knowledge_graph_builder;

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

  const redirectSlug =
    run.status === "duplicate" &&
    run.replay_payload &&
    typeof run.replay_payload === "object" &&
    "redirect_to_slug" in run.replay_payload
      ? String(run.replay_payload.redirect_to_slug)
      : null;

  const showRich =
    run.status === "completed" ||
    run.status === "completed_with_warnings" ||
    (run.status === "running" && Object.keys(agentResults).length > 0);

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

      {redirectSlug && (
        <div
          className="status"
          style={{
            marginBottom: "1rem",
            padding: "0.75rem 1rem",
            borderRadius: 8,
            background: "rgba(251, 191, 36, 0.12)",
            border: "1px solid rgba(251, 191, 36, 0.35)",
          }}
        >
          <p style={{ margin: "0 0 0.5rem" }}>
            A similar analysis was recently completed (same company, files, and
            track).
          </p>
          <Link to={`/analysis/${redirectSlug}`} className="btn-primary">
            View existing analysis
          </Link>
          <p
            style={{
              margin: "0.75rem 0 0",
              fontSize: "0.85rem",
              color: "var(--text-muted)",
            }}
          >
            To force a new run, start again from Upload and enable “Force new
            run” (or wait 24h).
          </p>
        </div>
      )}

      <h1 style={{ marginTop: 0 }}>Analysis</h1>
      <p style={{ color: "var(--text-muted)", marginTop: "-0.5rem" }}>
        Run <code className="inline-code">{run.slug}</code> · {run.status}
        {run.track ? ` · ${run.track}` : ""}
      </p>

      <div
        style={{
          display: "flex",
          gap: "0.5rem",
          flexWrap: "wrap",
          marginBottom: "1rem",
        }}
      >
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

      {(run.status === "running" || run.status === "pending") && (
        <div
          style={{
            marginBottom: "1rem",
            padding: "0.75rem",
            borderRadius: 8,
            background: "var(--surface-1, #1e293b)",
          }}
        >
          <strong>Analysis in progress</strong>
          <p
            style={{
              margin: "0.35rem 0 0",
              fontSize: "0.9rem",
              color: "var(--text-muted)",
            }}
          >
            This page refreshes every few seconds. Charts appear when agents
            finish.
          </p>
        </div>
      )}

      {run.summary && <div className="analysis-summary">{run.summary}</div>}

      {showRich && run.track && (
        <>
          <div style={{ display: "flex", gap: "0.5rem", marginTop: "1.25rem" }}>
            <button
              type="button"
              className={tab === "analysis" ? "btn-primary" : "btn-secondary"}
              onClick={() => setTab("analysis")}
            >
              Charts &amp; insights
            </button>
            {kg?.nodes && kg.nodes.length > 0 && (
              <button
                type="button"
                className={tab === "graph" ? "btn-primary" : "btn-secondary"}
                onClick={() => setTab("graph")}
              >
                Knowledge graph
              </button>
            )}
          </div>
          {tab === "analysis" && (
            <TrackRenderer
              track={run.track}
              agentResults={agentResults}
              visualizationPlan={vizPlan}
              slug={run.slug}
            />
          )}
          {tab === "graph" && kg?.nodes && kg.nodes.length > 0 && (
            <div style={{ marginTop: "1rem", minHeight: 400 }}>
              <KnowledgeGraphViewer
                nodes={kg.nodes}
                edges={kg.edges ?? []}
                clusters={kg.clusters ?? []}
              />
            </div>
          )}
        </>
      )}

      <Collapsible title="Agent activity" defaultOpen={false}>
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
      </Collapsible>

      <Collapsible title="Pipeline log" defaultOpen={false}>
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
      </Collapsible>

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
