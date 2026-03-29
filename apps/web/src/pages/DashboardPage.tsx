import { useCallback, useEffect, useMemo, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../contexts/AuthContext";
import {
  deletePipelineRun,
  listPipelineRuns,
  listUploadedFiles,
  startPipelineRun,
  stopActiveRuns,
  stopPipelineRun,
  type PipelineRun,
} from "../lib/api";
import {
  onboardingPathToAnalysisTrackId,
  trackIdToStartOnboarding,
} from "../lib/trackOnboarding";

const TRACK_BADGE: Record<string, string> = {
  predictive: "#3b82f6",
  automation: "#22c55e",
  optimization: "#f97316",
  supply_chain: "#a855f7",
  custom_analysis: "#14b8a6",
};

function trackBadgeColor(track: string | null | undefined): string {
  if (!track) return "#64748b";
  return TRACK_BADGE[track] ?? "#64748b";
}

function isActiveRunStatus(status: string): boolean {
  return status === "running" || status === "pending";
}

function runListHeading(r: PipelineRun): string {
  const t = (r.analysis_title ?? "").trim();
  return t || r.slug;
}

function confidenceFromRun(r: PipelineRun): number | null {
  const rp = r.replay_payload;
  if (!rp || typeof rp !== "object") return null;
  const vp = rp.visualization_plan as
    | { overall_confidence?: number }
    | undefined;
  if (vp && typeof vp.overall_confidence === "number")
    return vp.overall_confidence;
  const fr = rp.final_report as
    | { visualization_plan?: { overall_confidence?: number } }
    | undefined;
  const oc = fr?.visualization_plan?.overall_confidence;
  return typeof oc === "number" ? oc : null;
}

export default function DashboardPage() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [runs, setRuns] = useState<PipelineRun[]>([]);
  const [trackFilter, setTrackFilter] = useState<string>("");
  const [loading, setLoading] = useState(true);
  const [starting, setStarting] = useState(false);
  const [stopping, setStopping] = useState(false);
  const [slugDeleting, setSlugDeleting] = useState<string | null>(null);
  const [slugStopping, setSlugStopping] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      setRuns(await listPipelineRuns());
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load analyses");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  const filteredRuns = useMemo(() => {
    if (!trackFilter) return runs;
    return runs.filter((r) => (r.track || "") === trackFilter);
  }, [runs, trackFilter]);

  const completed = runs.filter(
    (r) => r.status === "completed" || r.status === "completed_with_warnings",
  ).length;
  const running = runs.filter(
    (r) => r.status === "running" || r.status === "pending",
  ).length;

  const avgConfidence = useMemo(() => {
    const done = runs.filter(
      (r) => r.status === "completed" || r.status === "completed_with_warnings",
    );
    const vals = done
      .map(confidenceFromRun)
      .filter((x): x is number => x != null);
    if (!vals.length) return null;
    return vals.reduce((a, b) => a + b, 0) / vals.length;
  }, [runs]);

  async function handleStartFlow() {
    setStarting(true);
    setError(null);
    try {
      if (user?.public_scrape_enabled) {
        const run = await startPipelineRun({ uploaded_file_ids: [] });
        navigate(`/analysis/${run.slug}`);
        return;
      }
      navigate("/upload");
    } catch (e) {
      setError(e instanceof Error ? e.message : "Could not start analysis");
    } finally {
      setStarting(false);
    }
  }

  async function handleDeleteRun(slug: string) {
    if (
      !window.confirm(
        "Remove this analysis from your list? This cannot be undone.",
      )
    ) {
      return;
    }
    setSlugDeleting(slug);
    setError(null);
    try {
      await deletePipelineRun(slug);
      await refresh();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Could not delete analysis");
    } finally {
      setSlugDeleting(null);
    }
  }

  async function handleStopRun(slug: string) {
    setSlugStopping(slug);
    setError(null);
    try {
      await stopPipelineRun(slug);
      await refresh();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Could not stop analysis");
    } finally {
      setSlugStopping(null);
    }
  }

  async function handleStopActiveAnalyses() {
    setStopping(true);
    setError(null);
    try {
      await stopActiveRuns();
      await refresh();
    } catch (e) {
      setError(
        e instanceof Error ? e.message : "Could not stop active analyses",
      );
    } finally {
      setStopping(false);
    }
  }

  async function handleStartAnother() {
    setStarting(true);
    setError(null);
    try {
      const trackId = onboardingPathToAnalysisTrackId(user?.onboarding_path);
      const files = await listUploadedFiles(trackId);
      const ids = files.map((f) => f.id);
      if (!ids.length && !user?.public_scrape_enabled) {
        navigate("/upload");
        return;
      }
      const payload = !ids.length && user?.public_scrape_enabled ? [] : ids;
      const run = await startPipelineRun({
        uploaded_file_ids: payload,
        onboarding_path: trackIdToStartOnboarding(trackId),
      });
      navigate(`/analysis/${run.slug}`);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Could not start analysis");
    } finally {
      setStarting(false);
    }
  }

  return (
    <div>
      <h1 style={{ marginTop: 0 }}>Welcome back, {user?.name ?? "there"}!</h1>
      <div className="dashboard-stat-rows">
        <div className="dashboard-stat-row">
          <div className="stat-card">
            <h3>Total analyses</h3>
            <div className="stat-value">{runs.length}</div>
          </div>
          <div className="stat-card">
            <h3>Completed</h3>
            <div className="stat-value">{completed}</div>
          </div>
        </div>
        <div className="dashboard-stat-row">
          <div className="stat-card">
            <h3>In progress</h3>
            <div
              className="stat-value"
              style={{
                fontSize: "1.25rem",
                color: running > 0 ? "#fbbf24" : "#4ade80",
              }}
            >
              {running > 0 ? `${running} running` : "Idle"}
            </div>
          </div>
          <div className="stat-card">
            <h3>Avg confidence</h3>
            <div className="stat-value">
              {avgConfidence != null
                ? `${(avgConfidence * 100).toFixed(0)}%`
                : "—"}
            </div>
          </div>
        </div>
      </div>

      {error && (
        <div
          className="status error"
          style={{
            margin: "1rem 0",
            padding: "0.6rem 0.75rem",
            borderRadius: 6,
          }}
        >
          {error}
        </div>
      )}

      <div
        className="dashboard-actions"
        style={{
          display: "flex",
          flexWrap: "wrap",
          gap: "0.75rem",
          marginBottom: "1.5rem",
          alignItems: "center",
        }}
      >
        {runs.length === 0 ? (
          <button
            type="button"
            className="btn-primary"
            disabled={starting}
            onClick={() => void handleStartFlow()}
          >
            {starting ? "Starting…" : "Start your first analysis"}
          </button>
        ) : (
          <button
            type="button"
            className="btn-primary"
            disabled={starting}
            onClick={() => void handleStartAnother()}
          >
            {starting ? "Starting…" : "Start analysis"}
          </button>
        )}
        <Link
          to="/upload"
          className="btn-secondary"
          style={{ display: "inline-flex", alignItems: "center" }}
        >
          New analysis (upload)
        </Link>
        <div className="dashboard-track-filter">
          <span id="dashboard-track-filter-label">Filter track</span>
          <select
            id="dashboard-track-filter"
            aria-labelledby="dashboard-track-filter-label"
            value={trackFilter}
            onChange={(e) => setTrackFilter(e.target.value)}
            className="dashboard-track-select"
          >
            <option value="">All tracks</option>
            <option value="predictive">Predictive</option>
            <option value="automation">Automation</option>
            <option value="optimization">Optimization</option>
            <option value="supply_chain">Supply chain</option>
            <option value="custom_analysis">Custom analysis</option>
          </select>
        </div>
        <button
          type="button"
          className="btn-secondary"
          disabled={stopping}
          title="Immediately terminates running pipeline workers (including in-flight model calls), then marks those runs cancelled in the database. Use before starting a new analysis or clearing history."
          onClick={() => void handleStopActiveAnalyses()}
          style={{
            borderColor: "rgba(248, 113, 113, 0.55)",
            color: "#fca5a5",
          }}
        >
          {stopping ? "Force stopping…" : "Force stop active analyses"}
        </button>
      </div>

      <h2 className="section-title">Company analyses</h2>
      {loading ? (
        <div className="spinner-page" style={{ minHeight: 120 }}>
          <div className="spinner" />
        </div>
      ) : filteredRuns.length === 0 ? (
        <div className="empty-state">
          <p>
            No analyses match this filter. Adjust the track filter or start a
            new run.
          </p>
        </div>
      ) : (
        <ul className="analysis-run-list">
          {filteredRuns.map((r) => {
            const conf = confidenceFromRun(r);
            const active = isActiveRunStatus(r.status);
            const cancelled = r.status === "cancelled";
            return (
              <li key={r.id} className="analysis-run-card">
                <div>
                  <div
                    style={{
                      display: "flex",
                      alignItems: "center",
                      gap: "0.5rem",
                      flexWrap: "wrap",
                    }}
                  >
                    {cancelled ? (
                      <span
                        className="analysis-run-link"
                        style={{
                          textDecoration: "line-through",
                          opacity: 0.65,
                          cursor: "not-allowed",
                          pointerEvents: "none",
                        }}
                        title="This analysis was cancelled"
                      >
                        {runListHeading(r)}
                      </span>
                    ) : (
                      <Link
                        to={`/analysis/${r.slug}`}
                        className="analysis-run-link"
                      >
                        {runListHeading(r)}
                      </Link>
                    )}
                    {r.track && (
                      <span
                        className="inline-code"
                        style={{
                          background: trackBadgeColor(r.track),
                          color: "#0f172a",
                          border: "none",
                          fontSize: "0.7rem",
                          textTransform: "capitalize",
                        }}
                      >
                        {r.track.replace("_", " ")}
                      </span>
                    )}
                    <span
                      className="analysis-run-meta"
                      style={{
                        color:
                          r.status === "running" || r.status === "pending"
                            ? "#fbbf24"
                            : undefined,
                      }}
                    >
                      {r.status}
                    </span>
                  </div>
                  <p className="analysis-run-meta">
                    {(r.analysis_title ?? "").trim() ? (
                      <>
                        <code
                          className="inline-code"
                          style={{
                            opacity: 0.55,
                            fontSize: "0.78rem",
                            fontWeight: 400,
                          }}
                        >
                          {r.slug}
                        </code>
                        {" · "}
                      </>
                    ) : null}
                    {r.started_by_name ? `${r.started_by_name} · ` : ""}
                    {r.started_at}
                  </p>
                  {r.summary && (
                    <p className="analysis-run-summary">
                      {r.summary.length > 140
                        ? `${r.summary.slice(0, 140)}…`
                        : r.summary}
                    </p>
                  )}
                  {conf != null && (
                    <p
                      style={{
                        fontSize: "0.8rem",
                        color: "var(--text-muted)",
                        margin: "0.25rem 0 0",
                      }}
                    >
                      Confidence {(conf * 100).toFixed(0)}%
                    </p>
                  )}
                </div>
                <div className="analysis-run-card-actions">
                  {cancelled ? (
                    <span
                      className="analysis-run-open-disabled"
                      aria-disabled="true"
                      title="Open is not available for cancelled analyses"
                    >
                      Open
                    </span>
                  ) : (
                    <Link to={`/analysis/${r.slug}`} className="btn-secondary">
                      Open
                    </Link>
                  )}
                  {active && (
                    <button
                      type="button"
                      className="btn-secondary"
                      disabled={slugStopping === r.slug}
                      title="Immediately terminates this run’s worker, then marks it cancelled."
                      onClick={() => void handleStopRun(r.slug)}
                      style={{
                        borderColor: "rgba(248, 113, 113, 0.55)",
                        color: "#fca5a5",
                      }}
                    >
                      {slugStopping === r.slug ? "Stopping…" : "Force stop"}
                    </button>
                  )}
                  {!active && (
                    <button
                      type="button"
                      className="btn-secondary"
                      disabled={slugDeleting === r.slug}
                      title="Remove this analysis from your list"
                      onClick={() => void handleDeleteRun(r.slug)}
                      style={{
                        borderColor: "rgba(248, 113, 113, 0.55)",
                        color: "#fca5a5",
                      }}
                    >
                      {slugDeleting === r.slug ? "Removing…" : "Delete"}
                    </button>
                  )}
                </div>
              </li>
            );
          })}
        </ul>
      )}
    </div>
  );
}
