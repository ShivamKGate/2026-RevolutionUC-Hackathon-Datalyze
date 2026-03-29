import { useCallback, useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../contexts/AuthContext";
import {
  listUploadedFiles,
  postDatalyzeChat,
  uploadDataFile,
  type UploadedFile,
} from "../lib/api";
import "../components/analysis/analysis.css";

type ChatMsg = { role: "user" | "assistant"; content: string };

const BASE_TRACKS = [
  {
    id: "auto",
    label: "Auto (recommended)",
    hint: "Picks pipeline from your goal, files, and public-scrape setting",
  },
  {
    id: "predictive",
    label: "Predictive / trends",
    hint: "Forecasts, KPI projections, time-series style analysis",
  },
  {
    id: "automation",
    label: "Automation strategy",
    hint: "DevOps, workflows, automation opportunities",
  },
  {
    id: "optimization",
    label: "Business optimization",
    hint: "Operational efficiency and org-wide improvements",
  },
  {
    id: "supply_chain",
    label: "Supply chain",
    hint: "Logistics, inventory, suppliers, fulfillment",
  },
] as const;

export default function DatalyzeChatPage() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [files, setFiles] = useState<UploadedFile[]>([]);
  const [selectedIds, setSelectedIds] = useState<number[]>([]);
  const [pickerOpen, setPickerOpen] = useState(false);
  const [publicScrape, setPublicScrape] = useState(() =>
    Boolean(user?.public_scrape_enabled),
  );
  const [baseTrack, setBaseTrack] = useState<string>("auto");
  const [messages, setMessages] = useState<ChatMsg[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [uploadBusy, setUploadBusy] = useState(false);
  const [dragOver, setDragOver] = useState(false);

  const refreshFiles = useCallback(async () => {
    setFiles(await listUploadedFiles(null));
  }, []);

  useEffect(() => {
    void refreshFiles();
  }, [refreshFiles]);

  function toggleFile(id: number) {
    setSelectedIds((prev) =>
      prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id],
    );
  }

  async function onDropFiles(fileList: FileList | File[]) {
    const arr = Array.from(fileList);
    if (!arr.length) return;
    setUploadBusy(true);
    setError(null);
    try {
      for (const f of arr) {
        const up = await uploadDataFile(f, null);
        setSelectedIds((prev) =>
          prev.includes(up.id) ? prev : [...prev, up.id],
        );
      }
      await refreshFiles();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Upload failed");
    } finally {
      setUploadBusy(false);
    }
  }

  async function send() {
    const text = input.trim();
    if (!text || loading) return;
    setError(null);
    const prev = messages;
    const next: ChatMsg[] = [...prev, { role: "user", content: text }];
    setMessages(next);
    setInput("");
    setLoading(true);
    try {
      const res = await postDatalyzeChat({
        messages: next.map((m) => ({
          role: m.role,
          content: m.content,
        })),
        uploaded_file_ids: selectedIds,
        enable_public_scrape: publicScrape,
        custom_base_track: baseTrack,
      });
      setMessages([...next, { role: "assistant", content: res.reply }]);
      if (res.started_run?.slug) {
        navigate(`/analysis/${res.started_run.slug}`);
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : "Chat failed");
      setMessages(prev);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="datalyze-chat-page">
      <div style={{ marginBottom: "1rem" }}>
        <Link to="/dashboard" className="nav-btn nav-btn-ghost">
          ← Dashboard
        </Link>
      </div>

      <h1 style={{ marginTop: 0 }}>Datalyze Chat</h1>
      <p style={{ color: "var(--text-muted)", marginTop: "-0.25rem" }}>
        Describe the custom analysis you want. With Base pipeline set to Auto
        (default), we pick predictive, automation, optimization, or supply chain
        from your instructions, the files you attach, upload metadata, and
        whether public scraping is enabled—then run the same full orchestrator
        against your goal. You can still pin a pipeline manually if you prefer.
      </p>

      {error && (
        <p className="status error" style={{ margin: "0.75rem 0" }}>
          {error}
        </p>
      )}

      <div className="datalyze-chat-toolbar">
        <button
          type="button"
          className="btn-secondary"
          onClick={() => setPickerOpen(true)}
        >
          Select uploaded files…
        </button>
        <span style={{ fontSize: "0.85rem", color: "var(--text-muted)" }}>
          {selectedIds.length} file(s) selected
        </span>
        <label
          style={{
            display: "inline-flex",
            alignItems: "center",
            gap: "0.35rem",
            fontSize: "0.9rem",
            cursor: "pointer",
          }}
        >
          <input
            type="checkbox"
            checked={publicScrape}
            onChange={(e) => setPublicScrape(e.target.checked)}
          />
          Enable public scraping
        </label>
        <label style={{ fontSize: "0.9rem" }}>
          Base pipeline:{" "}
          <select
            className="form-input"
            style={{ display: "inline-block", width: "auto", minWidth: 220 }}
            value={baseTrack}
            onChange={(e) => setBaseTrack(e.target.value)}
            aria-label="Base pipeline or Auto"
          >
            {BASE_TRACKS.map((t) => (
              <option key={t.id} value={t.id} title={t.hint}>
                {t.label}
              </option>
            ))}
          </select>
        </label>
      </div>

      <div
        className={`datalyze-chat-dropzone ${dragOver ? "datalyze-chat-dropzone--active" : ""}`}
        onDragOver={(e) => {
          e.preventDefault();
          setDragOver(true);
        }}
        onDragLeave={() => setDragOver(false)}
        onDrop={(e) => {
          e.preventDefault();
          setDragOver(false);
          void onDropFiles(e.dataTransfer.files);
        }}
        onClick={() => {
          const el = document.getElementById(
            "datalyze-chat-local-file",
          ) as HTMLInputElement | null;
          el?.click();
        }}
        role="presentation"
      >
        <input
          id="datalyze-chat-local-file"
          type="file"
          multiple
          style={{ display: "none" }}
          accept=".csv,.xlsx,.xls,.json,.pdf,.txt,.md"
          onChange={(e) => {
            if (e.target.files) void onDropFiles(e.target.files);
            e.target.value = "";
          }}
        />
        {uploadBusy
          ? "Uploading…"
          : "Drop files here or click to browse your computer (uploads to your library)."}
      </div>

      <div className="datalyze-chat-thread">
        {messages.length === 0 && (
          <p style={{ color: "var(--text-muted)", margin: 0 }}>
            Example: “Run a full analysis on these sales CSVs and compare to
            public industry benchmarks for our region.”
          </p>
        )}
        {messages.map((m, i) => (
          <div
            key={`${i}-${m.role}`}
            className={
              m.role === "user"
                ? "analysis-chat-msg analysis-chat-msg--user"
                : "analysis-chat-msg analysis-chat-msg--assistant"
            }
            style={{ whiteSpace: "pre-wrap" }}
          >
            {m.content}
          </div>
        ))}
      </div>

      <form
        className="analysis-chat-form"
        style={{ marginTop: "0.75rem" }}
        onSubmit={(e) => {
          e.preventDefault();
          void send();
        }}
      >
        <textarea
          className="form-input analysis-chat-input"
          rows={3}
          placeholder="Ask for a custom analysis or clarify your goal…"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          disabled={loading}
        />
        <button
          type="submit"
          className="btn-primary"
          disabled={loading || !input.trim()}
        >
          {loading ? "…" : "Send"}
        </button>
      </form>

      {pickerOpen && (
        <div
          className="datalyze-chat-picker-backdrop"
          role="presentation"
          style={{
            position: "fixed",
            inset: 0,
            background: "rgba(0,0,0,0.55)",
            zIndex: 50,
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            padding: "1rem",
          }}
          onClick={() => setPickerOpen(false)}
        >
          <div
            role="dialog"
            aria-modal="true"
            aria-labelledby="datalyze-chat-picker-title"
            style={{
              borderRadius: 10,
              padding: "1rem",
              maxWidth: 520,
              width: "100%",
              background: "var(--bg-elevated, #1e293b)",
              color: "inherit",
              maxHeight: "90vh",
              overflow: "hidden",
              display: "flex",
              flexDirection: "column",
            }}
            onClick={(e) => e.stopPropagation()}
          >
            <div
              style={{
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
                marginBottom: "0.75rem",
              }}
            >
              <strong id="datalyze-chat-picker-title">
                Your uploaded files
              </strong>
              <button
                type="button"
                className="nav-btn nav-btn-ghost"
                onClick={() => setPickerOpen(false)}
              >
                Close
              </button>
            </div>
            <ul
              style={{
                listStyle: "none",
                padding: 0,
                margin: 0,
                maxHeight: 320,
                overflowY: "auto",
              }}
            >
              {files.length === 0 && (
                <li style={{ color: "var(--text-muted)" }}>No files yet.</li>
              )}
              {files.map((f) => (
                <li key={f.id} style={{ marginBottom: "0.35rem" }}>
                  <label
                    style={{
                      display: "flex",
                      alignItems: "center",
                      gap: "0.5rem",
                      cursor: "pointer",
                    }}
                  >
                    <input
                      type="checkbox"
                      checked={selectedIds.includes(f.id)}
                      onChange={() => toggleFile(f.id)}
                    />
                    <span>{f.original_filename}</span>
                    <span
                      style={{
                        fontSize: "0.75rem",
                        color: "var(--text-muted)",
                      }}
                    >
                      ({f.visibility})
                    </span>
                  </label>
                </li>
              ))}
            </ul>
          </div>
        </div>
      )}
    </div>
  );
}
