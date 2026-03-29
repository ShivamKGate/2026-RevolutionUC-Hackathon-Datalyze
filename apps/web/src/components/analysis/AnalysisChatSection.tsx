import { useState } from "react";
import { postAnalysisChat } from "../../lib/api";
import "./analysis.css";

type Msg = { role: "user" | "assistant"; content: string };

type Props = {
  slug: string;
};

export function AnalysisChatSection({ slug }: Props) {
  const [open, setOpen] = useState(false);
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState<Msg[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function send() {
    const text = input.trim();
    if (!text || loading) return;
    setError(null);
    const prev = messages;
    const next: Msg[] = [...prev, { role: "user", content: text }];
    setMessages(next);
    setInput("");
    setLoading(true);
    try {
      const { reply } = await postAnalysisChat(slug, next);
      setMessages([...next, { role: "assistant", content: reply }]);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Request failed");
      setMessages(prev);
    } finally {
      setLoading(false);
    }
  }

  return (
    <section
      className="analysis-detail-section analysis-detail-section--analysis-chat"
      aria-labelledby="analysis-chat-heading"
    >
      <details
        className="analysis-chat-panel"
        open={open}
        onToggle={(e) => setOpen((e.target as HTMLDetailsElement).open)}
      >
        <summary className="analysis-chat-summary">
          <header className="analysis-detail-outputs-heading analysis-chat-summary-text">
            <h2
              id="analysis-chat-heading"
              className="analysis-detail-outputs-title"
            >
              Analysis Chat
            </h2>
            <p className="analysis-detail-outputs-sub">
              Ask about this run using saved orchestrator memory and your source
              files as context. You cannot attach new files here.
            </p>
          </header>
          <span className="analysis-chat-toggle" aria-hidden>
            <span className="analysis-chat-chevron">{open ? "▼" : "▶"}</span>
            <span className="analysis-chat-toggle-label">
              {open ? "Collapse" : "Expand"}
            </span>
          </span>
        </summary>
        <div className="analysis-chat-body">
          {error && <p className="status error analysis-chat-error">{error}</p>}
          <div className="analysis-chat-log" aria-live="polite">
            {messages.length === 0 && (
              <p className="analysis-chat-empty">
                Example: “What did the aggregator highlight?” or “Summarize
                risks from the pipeline memory.”
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
              >
                {m.content}
              </div>
            ))}
          </div>
          <form
            className="analysis-chat-form"
            onSubmit={(e) => {
              e.preventDefault();
              void send();
            }}
          >
            <textarea
              className="form-input analysis-chat-input"
              rows={2}
              placeholder="Message about this analysis…"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              disabled={loading}
              aria-label="Analysis chat message"
            />
            <button
              type="submit"
              className="btn-primary"
              disabled={loading || !input.trim()}
            >
              {loading ? "Sending…" : "Send"}
            </button>
          </form>
          <p className="analysis-chat-footnote">
            Uses this run’s memory snapshot, a replay subset, and text excerpts
            from source files (not a live re-ingest).
          </p>
        </div>
      </details>
    </section>
  );
}
