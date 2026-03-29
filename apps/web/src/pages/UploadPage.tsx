import { useCallback, useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../contexts/AuthContext";
import UploadedFileList from "../components/uploads/UploadedFileList";
import {
  deleteUploadedFile,
  listUploadedFiles,
  startPipelineRun,
  uploadDataFile,
  type UploadedFile,
} from "../lib/api";

const ACCEPT =
  ".csv,.xlsx,.xls,.json,.pdf,.txt,.md,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet,application/vnd.ms-excel,text/csv,application/json";

const TRACKS = [
  {
    id: "predictive",
    label: "Predictive Deep Analysis",
    onboarding: "Deep Analysis",
  },
  {
    id: "automation",
    label: "Automation Strategy",
    onboarding: "DevOps/Automations",
  },
  {
    id: "optimization",
    label: "Business Optimization",
    onboarding: "Business Automations",
  },
  {
    id: "supply_chain",
    label: "Supply Chain & Operations",
    onboarding: "supply_chain",
  },
] as const;

export default function UploadPage() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const inputRef = useRef<HTMLInputElement>(null);
  const [track, setTrack] = useState<string>(TRACKS[0]!.id);
  const [files, setFiles] = useState<UploadedFile[]>([]);
  const [selectedIds, setSelectedIds] = useState<Set<number>>(new Set());
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [starting, setStarting] = useState(false);
  const [busyDelete, setBusyDelete] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [dragActive, setDragActive] = useState(false);
  const [forceNew, setForceNew] = useState(false);

  const refresh = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const list = await listUploadedFiles(track);
      setFiles(list);
      setSelectedIds(new Set(list.map((f) => f.id)));
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load files");
    } finally {
      setLoading(false);
    }
  }, [track]);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  function toggleSelect(id: number) {
    setSelectedIds((prev) => {
      const n = new Set(prev);
      if (n.has(id)) n.delete(id);
      else n.add(id);
      return n;
    });
  }

  function selectAll() {
    setSelectedIds(new Set(files.map((f) => f.id)));
  }

  function selectNone() {
    setSelectedIds(new Set());
  }

  async function handleFiles(fileList: FileList | null) {
    if (!fileList?.length) return;
    setUploading(true);
    setError(null);
    try {
      for (let i = 0; i < fileList.length; i += 1) {
        await uploadDataFile(fileList[i]!, track);
      }
      await refresh();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Upload failed");
    } finally {
      setUploading(false);
      if (inputRef.current) inputRef.current.value = "";
    }
  }

  async function handleDelete(id: number) {
    if (!window.confirm("Delete this file from your workspace?")) return;
    setBusyDelete(id);
    setError(null);
    try {
      await deleteUploadedFile(id);
      await refresh();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Delete failed");
    } finally {
      setBusyDelete(null);
    }
  }

  async function handleStartAnalysis() {
    const ids = files.filter((f) => selectedIds.has(f.id)).map((f) => f.id);
    if (!ids.length && !user?.public_scrape_enabled) {
      setError(
        "Select at least one file or enable public scrape in Company settings.",
      );
      return;
    }
    const meta = TRACKS.find((t) => t.id === track);
    setStarting(true);
    setError(null);
    try {
      const run = await startPipelineRun({
        uploaded_file_ids: ids,
        onboarding_path: meta?.onboarding,
        force_new: forceNew,
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
      <div className="upload-page-header">
        <h1 style={{ marginTop: 0 }}>Upload data</h1>
        {!user?.public_scrape_enabled && (
          <p className="upload-header-hint">
            Enable <strong>Transcrape public data</strong> in Settings → Company
            to start an analysis without uploads.
          </p>
        )}
      </div>

      <div style={{ marginBottom: "1.25rem", maxWidth: 480 }}>
        <label
          className="section-title"
          style={{ display: "block", marginBottom: "0.35rem" }}
        >
          Analysis track
        </label>
        <select
          className="btn-secondary"
          style={{ width: "100%", padding: "0.5rem 0.75rem" }}
          value={track}
          onChange={(e) => setTrack(e.target.value)}
        >
          {TRACKS.map((t) => (
            <option key={t.id} value={t.id}>
              {t.label}
            </option>
          ))}
        </select>
        <p
          style={{
            fontSize: "0.8rem",
            color: "var(--text-muted)",
            marginTop: "0.35rem",
          }}
        >
          Files are filtered to this track (plus untagged files). New uploads
          are tagged for this track.
        </p>
      </div>

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

      <div className="upload-toolbar">
        <button
          type="button"
          className="btn-primary"
          disabled={uploading}
          onClick={() => inputRef.current?.click()}
        >
          {uploading ? "Uploading…" : "Browse computer"}
        </button>
        <div
          className={"upload-drop-compact" + (dragActive ? " active" : "")}
          onDragEnter={(e) => {
            e.preventDefault();
            setDragActive(true);
          }}
          onDragOver={(e) => {
            e.preventDefault();
            setDragActive(true);
          }}
          onDragLeave={() => setDragActive(false)}
          onDrop={(e) => {
            e.preventDefault();
            setDragActive(false);
            void handleFiles(e.dataTransfer.files);
          }}
        >
          <span className="upload-drop-label">Drop files here</span>
        </div>
      </div>
      <input
        ref={inputRef}
        type="file"
        hidden
        multiple
        accept={ACCEPT}
        onChange={(e) => void handleFiles(e.target.files)}
      />
      <p
        style={{
          fontSize: "0.8rem",
          color: "var(--text-muted)",
          marginTop: "0.5rem",
        }}
      >
        Supported: CSV, Excel (.xlsx), JSON, PDF, text.
      </p>

      <div
        style={{
          display: "flex",
          flexWrap: "wrap",
          gap: "0.75rem",
          alignItems: "center",
          marginTop: "1.5rem",
        }}
      >
        <button
          type="button"
          className="btn-primary"
          disabled={
            starting || (!selectedIds.size && !user?.public_scrape_enabled)
          }
          onClick={() => void handleStartAnalysis()}
        >
          {starting ? "Starting…" : "Start analysis"}
        </button>
        <label
          style={{
            display: "flex",
            alignItems: "center",
            gap: "0.35rem",
            fontSize: "0.9rem",
          }}
        >
          <input
            type="checkbox"
            checked={forceNew}
            onChange={(e) => setForceNew(e.target.checked)}
          />
          Force new run (skip 24h duplicate redirect)
        </label>
      </div>

      <h2 className="section-title" style={{ marginTop: "2rem" }}>
        Your files ({selectedIds.size} selected)
      </h2>
      <div style={{ display: "flex", gap: "0.5rem", marginBottom: "0.75rem" }}>
        <button type="button" className="btn-secondary" onClick={selectAll}>
          Select all
        </button>
        <button type="button" className="btn-secondary" onClick={selectNone}>
          Deselect all
        </button>
      </div>
      {loading ? (
        <div className="spinner-page" style={{ minHeight: 120 }}>
          <div className="spinner" />
        </div>
      ) : (
        <UploadedFileList
          files={files}
          onDelete={handleDelete}
          busyId={busyDelete}
          selectable
          selectedIds={selectedIds}
          onToggleSelect={toggleSelect}
        />
      )}
    </div>
  );
}
