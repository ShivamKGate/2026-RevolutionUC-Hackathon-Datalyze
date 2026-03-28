import { useCallback, useEffect, useState } from "react";
import UploadedFileList from "../../components/uploads/UploadedFileList";
import {
  deleteUploadedFile,
  listUploadedFiles,
  type UploadedFile,
} from "../../lib/api";

export default function UploadedFilesPage() {
  const [files, setFiles] = useState<UploadedFile[]>([]);
  const [loading, setLoading] = useState(true);
  const [busyDelete, setBusyDelete] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);

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

  async function handleDelete(id: number) {
    if (!window.confirm("Delete this file?")) return;
    setBusyDelete(id);
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
      <h2 style={{ marginTop: 0 }}>Uploaded files</h2>
      <p style={{ color: "var(--text-muted)", marginBottom: "1.25rem" }}>
        Private files for your company workspace. You can also manage uploads
        from the Upload page.
      </p>
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
