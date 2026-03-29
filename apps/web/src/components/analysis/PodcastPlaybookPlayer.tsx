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

type Variant = "page" | "executive-inline";

/**
 * Plays ElevenLabs insight podcast (`narration.mp3`) with play / pause / stop / mute.
 * `executive-inline`: compact row beside confidence; seek bar expands while audio plays.
 */
export function PodcastPlaybookPlayer({
  slug,
  runStatus,
  variant = "page",
}: {
  slug: string;
  runStatus: string;
  variant?: Variant;
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

  const expandedChrome = finalReady && !paused;
  const inline = variant === "executive-inline";

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

  const rootClass = [
    "podcast-playbook",
    inline ? "podcast-playbook--executive-inline" : "podcast-playbook--page",
    inline && expandedChrome ? "podcast-playbook--expanded" : "",
  ]
    .filter(Boolean)
    .join(" ");

  return (
    <div className={rootClass}>
      <div className="podcast-playbook__brand-row">
        <span className="podcast-playbook__kicker">Insight podcast</span>
        <span
          className="podcast-playbook__ad"
          aria-label="Powered by ElevenLabs"
        >
          ElevenLabs
        </span>
      </div>

      {!finalReady && (
        <p className="podcast-playbook__status">
          {runStatus === "running" || runStatus === "pending"
            ? "Audio will be ready after the executive summary and narration step complete."
            : "Final narration is not available for this run."}
        </p>
      )}

      {loadError && (
        <p className="status error podcast-playbook__error">{loadError}</p>
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

          <div className="podcast-playbook__track-row">
            <span className="podcast-playbook__track-label">
              Full analysis summary
            </span>
            <div className="podcast-playbook__controls">
              <button
                type="button"
                className="btn-primary podcast-playbook__btn-play"
                onClick={() => void togglePlay()}
              >
                {paused ? "Play" : "Pause"}
              </button>
              <button type="button" className="btn-secondary" onClick={stop}>
                Stop
              </button>
              <label className="podcast-playbook__mute">
                <input
                  type="checkbox"
                  checked={muted}
                  onChange={(e) => setMuted(e.target.checked)}
                />
                Mute
              </label>
              <span className="podcast-playbook__time">
                {formatTime(currentTime)} / {formatTime(duration)}
              </span>
            </div>
          </div>

          <div className="podcast-playbook__seek-wrap">
            <input
              type="range"
              min={0}
              max={100}
              step={0.05}
              value={pct}
              onChange={onScrub}
              aria-label="Playback position"
              className="podcast-playbook__seek"
            />
          </div>
        </>
      )}
    </div>
  );
}
