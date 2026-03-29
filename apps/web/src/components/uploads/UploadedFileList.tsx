import type { UploadedFile } from "../../lib/api";

function formatBytes(n: number): string {
  if (n < 1024) return `${n} B`;
  if (n < 1024 * 1024) return `${(n / 1024).toFixed(1)} KB`;
  return `${(n / (1024 * 1024)).toFixed(1)} MB`;
}

type Props = {
  files: UploadedFile[];
  onDelete: (id: number) => void;
  busyId?: number | null;
  selectable?: boolean;
  selectedIds?: Set<number>;
  onToggleSelect?: (id: number) => void;
};

export default function UploadedFileList({
  files,
  onDelete,
  busyId,
  selectable,
  selectedIds,
  onToggleSelect,
}: Props) {
  if (!files.length) {
    return (
      <p className="upload-empty-list" style={{ color: "var(--text-muted)" }}>
        No files uploaded yet for this track filter.
      </p>
    );
  }

  return (
    <ul className="upload-file-grid">
      {files.map((f) => (
        <li key={f.id} className="upload-file-card">
          {selectable && selectedIds && onToggleSelect && (
            <label className="upload-file-check">
              <input
                type="checkbox"
                checked={selectedIds.has(f.id)}
                onChange={() => onToggleSelect(f.id)}
              />
            </label>
          )}
          <div className="upload-file-card-main">
            <span className="upload-file-name" title={f.original_filename}>
              {f.original_filename}
            </span>
            <span className="upload-file-meta">
              {formatBytes(f.byte_size)} · {f.visibility}
              {f.analysis_track ? ` · ${f.analysis_track}` : ""}
            </span>
          </div>
          <button
            type="button"
            className="btn-ghost-danger"
            disabled={busyId === f.id}
            onClick={() => onDelete(f.id)}
          >
            {busyId === f.id ? "…" : "Delete"}
          </button>
        </li>
      ))}
    </ul>
  );
}
