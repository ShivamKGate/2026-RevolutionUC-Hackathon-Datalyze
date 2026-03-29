import {
  lazy,
  Suspense,
  useEffect,
  useMemo,
  useRef,
  useState,
  type ReactNode,
} from "react";
import { AnalysisErrorBoundary } from "../components/analysis/AnalysisErrorBoundary";
import { Link, useParams } from "react-router-dom";
import {
  generateRunTitle,
  getPipelineRun,
  getPipelineRunLogs,
  patchRunTitle,
  type PipelineRun,
  type PipelineRunLog,
} from "../lib/api";
import { ExecutiveSummarySection, TrackRenderer } from "../components/analysis";
import { ExportButton } from "../components/analysis/shared/ExportButton";
const OrchestrationModeling = lazy(() =>
  import("../components/analysis/orchestration/OrchestrationModeling").then(
    (m) => ({ default: m.OrchestrationModeling }),
  ),
);
import type {
  AgentResults,
  VisualizationPlan,
} from "../components/analysis/types";
// import { KnowledgeGraphViewer } from "../components/knowledge-graph/KnowledgeGraphViewer";
import { ConfidenceStrip } from "../components/analysis/shared/ConfidenceStrip";
import { PodcastPlaybookPlayer } from "../components/analysis/PodcastPlaybookPlayer";

/*
 * Retired: "Agent activity" list (live + completed). Status comes from orchestration + logs.
 * Restore with StatusPanel + map over viewRun.agent_activity (see agentActivityStatusClass).
 */
import { normalizeRunForView } from "../lib/runViewNormalize";
import { coerceConfidenceScore } from "../lib/renderSafe";
import {
  agentActivitySummary,
  completedPipelineSummary,
  formatStructuredLogLine,
  runningStepSummary,
} from "./analysisPipelineSummary";

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

function readSessionBool(key: string, fallback: boolean): boolean {
  if (typeof sessionStorage === "undefined") return fallback;
  const v = sessionStorage.getItem(key);
  if (v === "1") return true;
  if (v === "0") return false;
  return fallback;
}

function StatusPanel({
  title,
  defaultOpen,
  summaryLine,
  children,
  storageKey,
  open: openControlled,
  onOpenChange,
}: {
  title: string;
  defaultOpen?: boolean;
  summaryLine: string;
  children?: ReactNode;
  /** When omitted and panel is uncontrolled, open state is persisted here. */
  storageKey?: string;
  /** Controlled open state (e.g. link orchestration + pipeline panels). */
  open?: boolean;
  onOpenChange?: (open: boolean) => void;
}) {
  const controlled = openControlled !== undefined;
  const [internalOpen, setInternalOpen] = useState(() => {
    if (controlled) return Boolean(openControlled);
    if (storageKey && typeof sessionStorage !== "undefined") {
      return readSessionBool(storageKey, defaultOpen ?? false);
    }
    return defaultOpen ?? false;
  });

  const open = controlled ? Boolean(openControlled) : internalOpen;

  useEffect(() => {
    if (controlled || !storageKey || typeof sessionStorage === "undefined")
      return;
    sessionStorage.setItem(storageKey, open ? "1" : "0");
  }, [open, storageKey, controlled]);

  function toggle() {
    const next = !open;
    onOpenChange?.(next);
    if (!controlled) setInternalOpen(next);
  }

  return (
    <div className="analysis-status-panel">
      <button
        type="button"
        className="analysis-status-panel-toggle"
        aria-expanded={open}
        onClick={toggle}
      >
        <span className="analysis-status-chevron">{open ? "▼" : "▶"}</span>
        <span className="analysis-status-title">{title}</span>
        {!open && (
          <span className="analysis-status-summary" title={summaryLine}>
            {summaryLine.length > 120
              ? `${summaryLine.slice(0, 117)}…`
              : summaryLine}
          </span>
        )}
      </button>
      {open && <div className="analysis-status-panel-body">{children}</div>}
    </div>
  );
}

function LivePipelineLog({
  logs,
  pipelineLogLines,
}: {
  logs: PipelineRunLog[];
  pipelineLogLines: string[];
}) {
  const ref = useRef<HTMLPreElement>(null);
  const text = useMemo(() => {
    const structured =
      logs.length > 0
        ? logs
            .map((entry) => {
              const d = entry.detail;
              const detailStr =
                typeof d === "string" ? d : JSON.stringify(d ?? "");
              return `[${entry.timestamp ?? "n/a"}] [${entry.stage}] [${entry.agent}] ${entry.action}: ${detailStr}`;
            })
            .join("\n")
        : "";
    const legacyLines = pipelineLogLines.filter(Boolean);
    const legacy = legacyLines.length > 0 ? legacyLines.join("\n") : "";
    if (legacyLines.length > logs.length && legacyLines.length > 0) {
      return legacy;
    }
    if (logs.length > 0) {
      return structured;
    }
    return legacy;
  }, [logs, pipelineLogLines]);

  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    el.scrollTop = el.scrollHeight;
  }, [text]);

  return (
    <pre ref={ref} className="pipeline-log-block analysis-live-log-pre">
      {text || "Waiting for pipeline log entries…"}
    </pre>
  );
}

export default function AnalysisDetailPage() {
  const { slug } = useParams<{ slug: string }>();
  const linkedExecStorageKey = slug ? `${slug}:exec:linked` : "";
  const [executionPanelsOpen, setExecutionPanelsOpen] = useState(() =>
    linkedExecStorageKey ? readSessionBool(linkedExecStorageKey, false) : false,
  );

  useEffect(() => {
    if (!linkedExecStorageKey) return;
    setExecutionPanelsOpen(readSessionBool(linkedExecStorageKey, false));
  }, [linkedExecStorageKey]);

  useEffect(() => {
    if (!linkedExecStorageKey || typeof sessionStorage === "undefined") return;
    sessionStorage.setItem(
      linkedExecStorageKey,
      executionPanelsOpen ? "1" : "0",
    );
  }, [linkedExecStorageKey, executionPanelsOpen]);

  const [run, setRun] = useState<PipelineRun | null>(null);
  const [logs, setLogs] = useState<PipelineRunLog[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);
  const [titleDraft, setTitleDraft] = useState("");
  const [titleSaving, setTitleSaving] = useState(false);
  const [titleGenerating, setTitleGenerating] = useState(false);
  const [titleError, setTitleError] = useState<string | null>(null);
  const pollRef = useRef<number | undefined>(undefined);
  const liveFeedsAnchorRef = useRef<HTMLDivElement | null>(null);
  const liveScrollForSlugRef = useRef<string | null>(null);

  useEffect(() => {
    if (!slug) return;
    let cancelled = false;

    const load = async () => {
      try {
        const [r, logRows] = await Promise.all([
          getPipelineRun(slug),
          getPipelineRunLogs(slug),
        ]);
        if (cancelled) return;
        setRun(r);
        setTitleDraft(r.analysis_title ?? "");
        setLogs(logRows);
        setError(null);
        if (r.status === "pending" || r.status === "running") {
          if (pollRef.current == null) {
            pollRef.current = window.setInterval(() => {
              void load();
            }, 1000);
          }
        } else if (pollRef.current != null) {
          window.clearInterval(pollRef.current);
          pollRef.current = undefined;
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
      if (pollRef.current != null) {
        window.clearInterval(pollRef.current);
        pollRef.current = undefined;
      }
    };
  }, [slug]);

  const viewRun = useMemo(() => (run ? normalizeRunForView(run) : null), [run]);

  const isLiveRunScroll =
    viewRun?.status === "pending" || viewRun?.status === "running";

  useEffect(() => {
    liveScrollForSlugRef.current = null;
  }, [slug]);

  useEffect(() => {
    if (!isLiveRunScroll || !slug) return;
    if (liveScrollForSlugRef.current === slug) return;
    liveScrollForSlugRef.current = slug;
    const t = window.setTimeout(() => {
      liveFeedsAnchorRef.current?.scrollIntoView({
        behavior: "smooth",
        block: "start",
      });
    }, 120);
    return () => window.clearTimeout(t);
  }, [isLiveRunScroll, slug]);

  const agentResults = useMemo(
    () => (viewRun ? extractAgentResults(viewRun) : {}),
    [viewRun],
  );
  const vizPlan = useMemo(
    () => (viewRun ? extractVisualizationPlan(viewRun) : undefined),
    [viewRun],
  );
  const pipelineSummary = useMemo(() => {
    if (!viewRun) return "";
    if (viewRun.status === "pending" || viewRun.status === "running") {
      return runningStepSummary(logs, viewRun.pipeline_log);
    }
    if (
      viewRun.status === "completed" ||
      viewRun.status === "completed_with_warnings"
    ) {
      return completedPipelineSummary(logs, viewRun.pipeline_log);
    }
    const pl = viewRun.pipeline_log;
    return logs.length
      ? formatStructuredLogLine(logs[logs.length - 1]!)
      : (pl.filter(Boolean).slice(-1)[0] ?? "—");
  }, [viewRun, logs]);

  const activitySummary = useMemo(
    () => (viewRun ? agentActivitySummary(viewRun.agent_activity) : ""),
    [viewRun],
  );

  const headerConfidence = useMemo(() => {
    if (!viewRun) return null;
    if (vizPlan) {
      const raw = vizPlan as { overall_confidence?: unknown };
      const c = coerceConfidenceScore(
        raw.overall_confidence ?? (vizPlan as unknown),
      );
      if (c != null) return c;
    }
    const rp = viewRun.replay_payload;
    if (rp && typeof rp === "object") {
      const fr = rp.final_report as
        | { visualization_plan?: Record<string, unknown> }
        | undefined;
      const vp = fr?.visualization_plan;
      const c = coerceConfidenceScore(vp?.overall_confidence ?? vp);
      if (c != null) return c;
    }
    return null;
  }, [viewRun, vizPlan]);

  async function copyShareLink() {
    try {
      await navigator.clipboard.writeText(window.location.href);
      setCopied(true);
      window.setTimeout(() => setCopied(false), 1500);
    } catch {
      setCopied(false);
    }
  }

  async function handleSaveTitle() {
    if (!slug) return;
    setTitleSaving(true);
    setTitleError(null);
    try {
      const updated = await patchRunTitle(
        slug,
        titleDraft.trim() ? titleDraft.trim() : null,
      );
      setRun(updated);
      setTitleDraft(updated.analysis_title ?? "");
    } catch (e) {
      setTitleError(e instanceof Error ? e.message : "Save failed");
    } finally {
      setTitleSaving(false);
    }
  }

  async function handleGenerateTitle() {
    if (!slug) return;
    setTitleGenerating(true);
    setTitleError(null);
    try {
      const updated = await generateRunTitle(slug);
      setRun(updated);
      setTitleDraft(updated.analysis_title ?? "");
    } catch (e) {
      setTitleError(e instanceof Error ? e.message : "Generation failed");
    } finally {
      setTitleGenerating(false);
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

  if (!run || !viewRun) {
    return (
      <div className="spinner-page">
        <div className="spinner" />
      </div>
    );
  }

  const redirectSlug =
    viewRun.status === "duplicate" &&
    viewRun.replay_payload &&
    typeof viewRun.replay_payload === "object" &&
    "redirect_to_slug" in viewRun.replay_payload
      ? String(viewRun.replay_payload.redirect_to_slug)
      : null;

  const showRich =
    viewRun.status === "completed" ||
    viewRun.status === "completed_with_warnings" ||
    (viewRun.status === "running" && Object.keys(agentResults).length > 0);

  const isLiveRun =
    viewRun.status === "pending" || viewRun.status === "running";

  const storageBase = viewRun.slug;

  /* Standalone knowledge graph card/tab retired — graph is shown inside 3D orchestration.
   * Kept for reference:
   * const embedKgInCompletedColumn = showRich && !isLiveRun && Boolean(kg?.nodes?.length);
   * const showKnowledgeGraphTab = Boolean(kg?.nodes?.length) && !embedKgInCompletedColumn;
   */

  return (
    <AnalysisErrorBoundary>
      <div className="analysis-detail-page">
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
              A similar analysis was recently completed (same company, files,
              and track).
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

        {(() => {
          const displayTitle = (viewRun.analysis_title ?? "").trim();
          const canTitleTools =
            viewRun.status === "completed" ||
            viewRun.status === "completed_with_warnings";
          const showInsightPodcast =
            viewRun.status === "pending" ||
            viewRun.status === "running" ||
            viewRun.status === "completed" ||
            viewRun.status === "completed_with_warnings";
          return (
            <>
              <div className="analysis-detail-head-row">
                <div className="analysis-detail-head-main">
                  <h1 style={{ marginTop: 0 }}>{displayTitle || "Analysis"}</h1>
                  <p
                    style={{
                      color: "var(--text-muted)",
                      marginTop: "-0.35rem",
                      marginBottom: 0,
                    }}
                  >
                    {displayTitle ? (
                      <>
                        <span className="analysis-detail-id-faint">
                          <code className="inline-code">{viewRun.slug}</code>
                        </span>
                        {" · "}
                      </>
                    ) : (
                      <>
                        Run <code className="inline-code">{viewRun.slug}</code>{" "}
                        ·{" "}
                      </>
                    )}
                    {viewRun.status}
                    {viewRun.track ? ` · ${viewRun.track}` : ""}
                  </p>
                </div>
                {showInsightPodcast && (
                  <div className="analysis-detail-head-insights">
                    <PodcastPlaybookPlayer
                      slug={viewRun.slug}
                      runStatus={viewRun.status}
                      variant="executive-inline"
                    />
                  </div>
                )}
                {headerConfidence != null && (
                  <div className="analysis-detail-head-confidence">
                    <ConfidenceStrip
                      variant="header"
                      score={headerConfidence}
                      breakdown={
                        agentResults.output_evaluator?.confidence_breakdown
                      }
                    />
                  </div>
                )}
              </div>

              {canTitleTools && (
                <div className="analysis-title-toolbar">
                  {titleError && (
                    <div
                      className="status error"
                      style={{
                        flex: "1 1 100%",
                        margin: 0,
                        padding: "0.5rem 0.65rem",
                        borderRadius: 6,
                      }}
                    >
                      {titleError}
                    </div>
                  )}
                  <input
                    type="text"
                    className="form-input analysis-title-input"
                    placeholder="Optional title (shown on dashboard)"
                    aria-label="Analysis title"
                    value={titleDraft}
                    onChange={(e) => setTitleDraft(e.target.value)}
                    maxLength={500}
                  />
                  <button
                    type="button"
                    className="btn-secondary"
                    disabled={titleGenerating}
                    onClick={() => void handleGenerateTitle()}
                  >
                    {titleGenerating ? "Generating…" : "Generate title"}
                  </button>
                  <button
                    type="button"
                    className="btn-primary"
                    disabled={
                      titleSaving ||
                      titleDraft.trim() ===
                        (viewRun.analysis_title ?? "").trim()
                    }
                    onClick={() => void handleSaveTitle()}
                  >
                    {titleSaving ? "Saving…" : "Save title"}
                  </button>
                </div>
              )}
            </>
          );
        })()}

        <div
          style={{
            display: "flex",
            gap: "0.5rem",
            flexWrap: "wrap",
            marginBottom: "1rem",
            alignItems: "center",
          }}
        >
          <button
            type="button"
            className="btn-secondary"
            onClick={() => void copyShareLink()}
          >
            Copy share link
          </button>
          {showRich && viewRun.track && <ExportButton slug={viewRun.slug} />}
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

        {isLiveRun && (
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
              Orchestration and pipeline log update live below (this page polls
              about every second). Charts and exports unlock as agents complete.
            </p>
          </div>
        )}

        {viewRun.summary && (
          <div className="analysis-summary">{viewRun.summary}</div>
        )}

        {isLiveRun && (
          <section
            className="analysis-detail-section analysis-detail-section--execution"
            aria-labelledby="section-live-execution-heading"
          >
            <h2
              id="section-live-execution-heading"
              className="analysis-detail-section-heading"
            >
              Run execution
            </h2>
            <p className="analysis-detail-section-lead">
              Live orchestration model and pipeline log; this area updates while
              the run is in progress.
            </p>
            <div className="analysis-detail-section-rule" aria-hidden />
            <div
              ref={liveFeedsAnchorRef}
              className="analysis-live-feeds"
              aria-live="polite"
            >
              <section
                className="analysis-live-feed-column analysis-live-feed-column--orch"
                aria-labelledby="live-feed-orch-heading"
              >
                <h2
                  id="live-feed-orch-heading"
                  className="analysis-live-feed-heading"
                >
                  Orchestration (live)
                </h2>
                <p className="analysis-live-feed-sub">
                  {activitySummary || "Waiting for orchestrator and agents…"}
                </p>
                <div className="analysis-live-feed-body-grow">
                  <Suspense
                    fallback={
                      <p
                        className="analysis-live-empty"
                        style={{ margin: "1rem 0" }}
                      >
                        Loading orchestration view…
                      </p>
                    }
                  >
                    <OrchestrationModeling
                      run={viewRun}
                      logs={logs}
                      agentResults={agentResults}
                      storagePrefix={storageBase}
                      embedded
                      live
                    />
                  </Suspense>
                </div>
              </section>
              <section
                className="analysis-live-feed-column"
                aria-labelledby="live-feed-log-heading"
              >
                <h2
                  id="live-feed-log-heading"
                  className="analysis-live-feed-heading"
                >
                  Pipeline log
                </h2>
                <p className="analysis-live-feed-sub">{pipelineSummary}</p>
                <div className="analysis-live-log-shell">
                  <LivePipelineLog
                    logs={logs}
                    pipelineLogLines={viewRun.pipeline_log}
                  />
                </div>
              </section>
            </div>
          </section>
        )}

        {showRich && !isLiveRun && (
          <section
            className="analysis-detail-section analysis-detail-section--execution"
            aria-labelledby="section-run-execution-heading"
          >
            <h2
              id="section-run-execution-heading"
              className="analysis-detail-section-heading"
            >
              Run execution
            </h2>
            <p className="analysis-detail-section-lead">
              Orchestration model, structured pipeline log, and (when present)
              the knowledge graph for this run.
            </p>
            <div className="analysis-detail-section-rule" aria-hidden />
            <div className="analysis-completed-dual">
              <div className="analysis-completed-col-left">
                <StatusPanel
                  title="Orchestration & knowledge graph"
                  defaultOpen={false}
                  summaryLine="3D model, log scrubber, node details"
                  open={executionPanelsOpen}
                  onOpenChange={setExecutionPanelsOpen}
                >
                  <Suspense
                    fallback={
                      <p style={{ color: "var(--text-muted)" }}>
                        Loading orchestration view…
                      </p>
                    }
                  >
                    <OrchestrationModeling
                      run={viewRun}
                      logs={logs}
                      agentResults={agentResults}
                      storagePrefix={storageBase}
                      embedded
                    />
                  </Suspense>
                </StatusPanel>
              </div>
              <div className="analysis-completed-col-right">
                <StatusPanel
                  title="Pipeline log"
                  defaultOpen={false}
                  summaryLine={pipelineSummary}
                  open={executionPanelsOpen}
                  onOpenChange={setExecutionPanelsOpen}
                >
                  <pre className="pipeline-log-block">
                    {logs.length > 0
                      ? logs
                          .map((entry) => {
                            const d = entry.detail;
                            const detailStr =
                              typeof d === "string"
                                ? d
                                : JSON.stringify(d ?? "");
                            return `[${entry.timestamp ?? "n/a"}] [${entry.stage}] [${entry.agent}] ${entry.action}: ${detailStr}`;
                          })
                          .join("\n")
                      : viewRun.pipeline_log.join("\n")}
                  </pre>
                </StatusPanel>
              </div>
            </div>
            {/*
            Standalone 2D knowledge graph card (replaced by KG nodes in 3D orchestration view).
            {embedKgInCompletedColumn && kg?.nodes && (
              <div className="analysis-completed-kg-row">
                <StatusPanel
                  title="Knowledge graph (interactive)"
                  defaultOpen={false}
                  summaryLine={`${kg.nodes.length} nodes · ${(kg.edges ?? []).length} edges`}
                  storageKey={`${storageBase}:panel:kg-2d`}
                >
                  <div className="analysis-kg-panel-body">
                    <KnowledgeGraphViewer
                      nodes={kg.nodes}
                      edges={kg.edges ?? []}
                      clusters={kg.clusters ?? []}
                    />
                  </div>
                </StatusPanel>
              </div>
            )}
            */}
          </section>
        )}

        {showRich && viewRun.track && (
          <section
            className="analysis-detail-section analysis-detail-section--charts"
            aria-labelledby="section-analysis-outputs-heading"
          >
            <header className="analysis-detail-outputs-heading">
              <h2
                id="section-analysis-outputs-heading"
                className="analysis-detail-outputs-title"
              >
                Analysis outputs
              </h2>
              <p className="analysis-detail-outputs-sub">
                Recommendations, KPIs, charts, and summaries from this run.
              </p>
            </header>
            {/*
            <div className="analysis-detail-tab-bar">
              <button type="button" className="btn-primary">Charts & insights</button>
              <button type="button" className="btn-secondary">Knowledge graph</button>
            </div>
            {effectiveTab === "graph" && showKnowledgeGraphTab && kg?.nodes && (
              <div style={{ marginTop: "1rem", minHeight: 400 }}>
                <KnowledgeGraphViewer
                  nodes={kg.nodes}
                  edges={kg.edges ?? []}
                  clusters={kg.clusters ?? []}
                />
              </div>
            )}
            */}
            <TrackRenderer
              track={viewRun.track}
              agentResults={agentResults}
              visualizationPlan={vizPlan}
              slug={viewRun.slug}
              runStatus={viewRun.status}
              hideConfidenceStrip
            />
            {agentResults.executive_summary && (
              <div className="analysis-executive-finale">
                <ExecutiveSummarySection
                  data={agentResults.executive_summary}
                />
              </div>
            )}
          </section>
        )}

        {viewRun.run_dir_path && (
          <section
            className="analysis-detail-section analysis-detail-section--after"
            aria-labelledby="section-run-meta-heading"
          >
            <h2
              id="section-run-meta-heading"
              className="analysis-detail-section-heading analysis-detail-section-heading--subtle"
            >
              Additional details
            </h2>
            <div className="analysis-detail-section-rule" aria-hidden />
            <p className="analysis-detail-run-meta">
              Run artifacts:{" "}
              <code className="inline-code">{viewRun.run_dir_path}</code>
            </p>
          </section>
        )}
      </div>
    </AnalysisErrorBoundary>
  );
}
