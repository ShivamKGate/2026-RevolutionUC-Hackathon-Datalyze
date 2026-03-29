import { useCallback, useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../contexts/AuthContext";
import {
  listPipelineRuns,
  listUploadedFiles,
  startPipelineRun,
  type PipelineRun,
} from "../lib/api";

export default function DashboardPage() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [runs, setRuns] = useState<PipelineRun[]>([]);
  const [loading, setLoading] = useState(true);
  const [starting, setStarting] = useState(false);
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

  async function handleStartAnother() {
    setStarting(true);
    setError(null);
    try {
      const files = await listUploadedFiles();
      const ids = files.map((f) => f.id);
      if (!ids.length && !user?.public_scrape_enabled) {
        navigate("/upload");
        return;
      }
      const payload = !ids.length && user?.public_scrape_enabled ? [] : ids;
      const run = await startPipelineRun({ uploaded_file_ids: payload });
      navigate(`/analysis/${run.slug}`);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Could not start analysis");
    } finally {
      setStarting(false);
    }
  }

  const completed = runs.filter(
    (r) => r.status === "completed" || r.status === "completed_with_warnings",
  ).length;
  const running = runs.filter(
    (r) => r.status === "running" || r.status === "pending",
  ).length;

  return (
    <div>
      <h1 style={{ marginTop: 0 }}>Welcome back, {user?.name ?? "there"}!</h1>
      <div className="dashboard-grid">
        <div className="stat-card">
          <h3>Analyses</h3>
          <div className="stat-value">{runs.length}</div>
        </div>
        <div className="stat-card">
          <h3>Completed</h3>
          <div className="stat-value">{completed}</div>
        </div>
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
          Upload data
        </Link>
        <Link
          to="/pipeline"
          className="btn-secondary"
          style={{ display: "inline-flex", alignItems: "center" }}
        >
          Pipeline status
        </Link>
      </div>

      <h2 className="section-title">Your analyses</h2>
      {loading ? (
        <div className="spinner-page" style={{ minHeight: 120 }}>
          <div className="spinner" />
        </div>
      ) : runs.length === 0 ? (
        <div className="empty-state">
          <p>No analyses yet. Use the button above to start.</p>
        </div>
      ) : (
        <ul className="analysis-run-list">
          {runs.map((r) => (
            <li key={r.id} className="analysis-run-card">
              <div>
                <Link to={`/analysis/${r.slug}`} className="analysis-run-link">
                  {r.slug}
                </Link>
                <p className="analysis-run-meta">
                  {r.started_at} · {r.status}
                </p>
                {r.summary && (
                  <p className="analysis-run-summary">{r.summary}</p>
                )}
              </div>
              <Link to={`/analysis/${r.slug}`} className="btn-secondary">
                Open
              </Link>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
