import {
  useCallback,
  useEffect,
  useRef,
  useState,
  type ChangeEvent,
} from "react";
import { getNarrationManifest, narrationFinalUrl } from "../../lib/api";

function formatTime(sec: number): string {
  if (!Number.isFinite(sec) || sec < 0) return "0:00";
  const m = Math.floor(sec / 60);
  const s = Math.floor(sec % 60);
  return `${m}:${s.toString().padStart(2, "0")}`;
}

/**
 * After the run produces `narration.mp3`, plays the ElevenLabs insight podcast with
 * play / pause / stop. Mute toggles `HTMLAudioElement.muted` so unmute restores sound.
 */
export function PodcastPlaybookPlayer({
  slug,
  runStatus,
}: {
  slug: string;
  runStatus: string;
}) {
  const [finalReady, setFinalReady] = useState(false);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [muted, setMuted] = useState(false);
  const [duration, setDuration] = useState(0);
  const [currentTime, setCurrentTime] = useState(0);
  const [paused, setPaused] = useState(true);

  const audioRef = useRef<HTMLAudioElement | null>(null);

  const showPanel =
    runStatus === "pending" ||
    runStatus === "running" ||
    runStatus === "completed" ||
    runStatus === "completed_with_warnings";

  const poll = useCallback(async () => {
    try {
      const m = await getNarrationManifest(slug);
      setLoadError(null);
      if (m.final_narration) {
        setFinalReady(true);
        return true;
      }
    } catch {
      setLoadError("Could not check narration");
    }
    return false;
  }, [slug]);

  useEffect(() => {
    setFinalReady(false);
    setLoadError(null);
    setCurrentTime(0);
    setDuration(0);
    setPaused(true);
  }, [slug]);

  useEffect(() => {
    if (!showPanel || finalReady) return;

    let cancelled = false;
    void (async () => {
      const ok = await poll();
      if (!cancelled && ok) return;
    })();

    const id = window.setInterval(() => {
      void poll();
    }, 2000);

    return () => {
      cancelled = true;
      window.clearInterval(id);
    };
  }, [slug, showPanel, finalReady, poll]);

  useEffect(() => {
    const a = audioRef.current;
    if (a) a.muted = muted;
  }, [muted]);

  const stop = useCallback(() => {
    const a = audioRef.current;
    if (!a) return;
    a.pause();
    a.currentTime = 0;
    setPaused(true);
    setCurrentTime(0);
  }, []);

  const togglePlay = useCallback(async () => {
    const a = audioRef.current;
    if (!a || !finalReady) return;
    if (a.paused) {
      try {
        await a.play();
      } catch {
        setLoadError("Tap Play again if the browser blocked audio.");
      }
    } else {
      a.pause();
    }
  }, [finalReady]);

  const onScrub = useCallback(
    (e: ChangeEvent<HTMLInputElement>) => {
      const a = audioRef.current;
      if (!a || !duration) return;
      const t = (parseFloat(e.target.value) / 100) * duration;
      a.currentTime = t;
      setCurrentTime(t);
    },
    [duration],
  );

  if (!showPanel) return null;

  const pct = duration > 0 ? (currentTime / duration) * 100 : 0;

  return (
    <div
      className="podcast-playbook"
      style={{
        marginBottom: "1.25rem",
        padding: "clamp(0.75rem, 2vw, 1rem) clamp(1rem, 3vw, 1.25rem)",
        borderRadius: 12,
        background:
          "linear-gradient(145deg, rgba(15, 23, 42, 0.95), rgba(30, 27, 75, 0.88))",
        border: "1px solid rgba(167, 139, 250, 0.35)",
        boxShadow: "0 8px 32px rgba(0, 0, 0, 0.25)",
        maxWidth: "100%",
      }}
    >
      <div
        style={{
          display: "flex",
          flexWrap: "wrap",
          alignItems: "center",
          gap: "0.5rem 1rem",
          marginBottom: "0.75rem",
        }}
      >
        <span
          style={{
            fontSize: "0.7rem",
            textTransform: "uppercase",
            letterSpacing: "0.12em",
            color: "#c4b5fd",
            fontWeight: 600,
          }}
        >
          Insight podcast
        </span>
        <span style={{ fontSize: "0.9rem", color: "#e2e8f0" }}>
          ElevenLabs · full analysis summary
        </span>
      </div>

      {!finalReady && (
        <p
          style={{
            margin: "0 0 0.75rem",
            fontSize: "0.9rem",
            color: "var(--text-muted)",
          }}
        >
          {runStatus === "running" || runStatus === "pending"
            ? "Your audio playbook will appear here when the executive summary is ready."
            : "Final narration is not available for this run."}
        </p>
      )}

      {loadError && (
        <p className="status error" style={{ marginBottom: "0.5rem" }}>
          {loadError}
        </p>
      )}

      {finalReady && (
        <>
          <audio
            ref={audioRef}
            src={narrationFinalUrl(slug)}
            preload="metadata"
            muted={muted}
            onTimeUpdate={(e) => setCurrentTime(e.currentTarget.currentTime)}
            onDurationChange={(e) => {
              const d = e.currentTarget.duration;
              if (Number.isFinite(d)) setDuration(d);
            }}
            onEnded={() => {
              setPaused(true);
              setCurrentTime(0);
            }}
            onPlay={() => setPaused(false)}
            onPause={() => setPaused(true)}
          />

          <div
            style={{
              display: "flex",
              flexWrap: "wrap",
              alignItems: "center",
              gap: "0.5rem",
              marginBottom: "0.65rem",
            }}
          >
            <button
              type="button"
              className="btn-primary"
              style={{ minWidth: "5.5rem" }}
              onClick={() => void togglePlay()}
            >
              {paused ? "Play" : "Pause"}
            </button>
            <button type="button" className="btn-secondary" onClick={stop}>
              Stop
            </button>
            <label
              style={{
                display: "inline-flex",
                alignItems: "center",
                gap: "0.35rem",
                fontSize: "0.9rem",
                cursor: "pointer",
                marginLeft: "0.25rem",
              }}
            >
              <input
                type="checkbox"
                checked={muted}
                onChange={(e) => setMuted(e.target.checked)}
              />
              Mute
            </label>
            <span
              style={{
                fontSize: "0.85rem",
                color: "var(--text-muted)",
                fontVariantNumeric: "tabular-nums",
              }}
            >
              {formatTime(currentTime)} / {formatTime(duration)}
            </span>
          </div>

          <input
            type="range"
            min={0}
            max={100}
            step={0.05}
            value={pct}
            onChange={onScrub}
            aria-label="Playback position"
            style={{
              width: "100%",
              maxWidth: "100%",
              marginBottom: "0.25rem",
              cursor: "pointer",
            }}
          />
        </>
      )}
    </div>
  );
}
