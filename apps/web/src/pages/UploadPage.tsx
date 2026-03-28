import { useCallback, useEffect, useRef, useState } from "react";
import { useAuth } from "../contexts/AuthContext";
import UploadedFileList from "../components/uploads/UploadedFileList";
import {
  deleteUploadedFile,
  listUploadedFiles,
  uploadDataFile,
  type UploadedFile,
} from "../lib/api";

const ACCEPT =
  ".csv,.xlsx,.xls,.json,.pdf,.txt,.md,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet,application/vnd.ms-excel,text/csv,application/json";

export default function UploadPage() {
  const { user } = useAuth();
  const inputRef = useRef<HTMLInputElement>(null);
  const [files, setFiles] = useState<UploadedFile[]>([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [busyDelete, setBusyDelete] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [dragActive, setDragActive] = useState(false);

  const refresh = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      setFiles(await listUploadedFiles());
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load files");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  async function handleFiles(fileList: FileList | null) {
    if (!fileList?.length) return;
    setUploading(true);
    setError(null);
    try {
      for (let i = 0; i < fileList.length; i += 1) {
        await uploadDataFile(fileList[i]!);
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

  return (
    <div>
      <div className="upload-page-header">
        <h1 style={{ marginTop: 0 }}>Upload data</h1>
        {!user?.public_scrape_enabled && (
          <p className="upload-header-hint">
            Enable <strong>Transcrape public data</strong> in Settings → Company
            to start an analysis without uploading files (uses public context
            only — placeholder for now).
          </p>
        )}
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

      <h2 className="section-title" style={{ marginTop: "2rem" }}>
        Your files
      </h2>
      {loading ? (
        <div className="spinner-page" style={{ minHeight: 120 }}>
          <div className="spinner" />
        </div>
      ) : (
        <UploadedFileList
          files={files}
          onDelete={handleDelete}
          busyId={busyDelete}
        />
      )}
    </div>
  );
}
