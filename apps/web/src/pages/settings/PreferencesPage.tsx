import { useEffect, useState, type FormEvent } from "react";
import { useAuth } from "../../contexts/AuthContext";
import { updateUserPreferences } from "../../lib/api";
import { apiOnboardingPathToFormValue } from "../../lib/trackOnboarding";

const TRACK_OPTIONS = [
  { value: "deep_analysis", label: "Predictive / Deep Analysis" },
  { value: "automations", label: "Automation Strategy" },
  { value: "business_automations", label: "Business Optimization" },
  { value: "supply_chain", label: "Supply Chain & Operations" },
];

export default function PreferencesPage() {
  const { user, refreshUser } = useAuth();
  const [darkMode, setDarkMode] = useState(true);
  const [emailNotifications, setEmailNotifications] = useState(false);
  const [onboardingPath, setOnboardingPath] = useState("deep_analysis");
  const [savedTrack, setSavedTrack] = useState(false);
  const [savingTrack, setSavingTrack] = useState(false);
  const [trackError, setTrackError] = useState<string | null>(null);

  useEffect(() => {
    if (!user) return;
    setOnboardingPath(apiOnboardingPathToFormValue(user.onboarding_path));
  }, [user]);

  async function handleTrackSubmit(e: FormEvent) {
    e.preventDefault();
    setSavingTrack(true);
    setTrackError(null);
    setSavedTrack(false);
    try {
      await updateUserPreferences({
        onboarding_path: onboardingPath,
      });
      await refreshUser();
      setSavedTrack(true);
      window.setTimeout(() => setSavedTrack(false), 2000);
    } catch (err) {
      setTrackError(err instanceof Error ? err.message : "Save failed");
    } finally {
      setSavingTrack(false);
    }
  }

  return (
    <div>
      <h2 style={{ marginTop: 0 }}>Preferences</h2>
      <div
        style={{
          display: "flex",
          flexDirection: "column",
          gap: "1.5rem",
          maxWidth: 480,
        }}
      >
        <form
          onSubmit={handleTrackSubmit}
          style={{
            padding: "1.25rem",
            borderRadius: 10,
            border: "1px solid var(--border)",
            background: "var(--surface)",
            display: "flex",
            flexDirection: "column",
            gap: "1rem",
          }}
        >
          <div>
            <div style={{ fontWeight: 600, marginBottom: "0.35rem" }}>
              Default analysis track
            </div>
            <p
              style={{
                fontSize: "0.85rem",
                color: "var(--text-muted)",
                margin: "0 0 0.75rem",
              }}
            >
              Saved on your user account (not shared with other people in the
              company). Used for dashboard “Start analysis” and upload defaults.
            </p>
          </div>
          {trackError && (
            <div
              className="status error"
              style={{ margin: 0, padding: "0.6rem 0.75rem", borderRadius: 6 }}
            >
              {trackError}
            </div>
          )}
          <div className="form-group" style={{ margin: 0 }}>
            <label className="form-label" htmlFor="pref-track-path">
              Track
            </label>
            <select
              id="pref-track-path"
              className="form-input"
              value={onboardingPath}
              onChange={(e) => setOnboardingPath(e.target.value)}
            >
              {TRACK_OPTIONS.map((opt) => (
                <option key={opt.value} value={opt.value}>
                  {opt.label}
                </option>
              ))}
            </select>
          </div>
          <div style={{ display: "flex", alignItems: "center", gap: "1rem" }}>
            <button
              type="submit"
              className="btn-primary"
              disabled={savingTrack}
            >
              {savingTrack ? "Saving…" : "Save track preference"}
            </button>
            {savedTrack && (
              <span style={{ color: "#4ade80", fontSize: "0.875rem" }}>
                Saved!
              </span>
            )}
          </div>
        </form>

        <div
          style={{
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
          }}
        >
          <div>
            <div style={{ fontWeight: 500 }}>Dark Mode</div>
            <div style={{ fontSize: "0.8rem", color: "var(--text-muted)" }}>
              Use dark theme across the app
            </div>
          </div>
          <button
            type="button"
            onClick={() => setDarkMode((v) => !v)}
            style={{
              width: 44,
              height: 24,
              borderRadius: 12,
              border: "none",
              background: darkMode ? "var(--accent)" : "var(--border)",
              cursor: "pointer",
              position: "relative",
              transition: "background 0.2s",
            }}
          >
            <span
              style={{
                position: "absolute",
                top: 2,
                left: darkMode ? 22 : 2,
                width: 20,
                height: 20,
                borderRadius: "50%",
                background: "#fff",
                transition: "left 0.2s",
              }}
            />
          </button>
        </div>
        <div
          style={{
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
          }}
        >
          <div>
            <div style={{ fontWeight: 500 }}>Email Notifications</div>
            <div style={{ fontSize: "0.8rem", color: "var(--text-muted)" }}>
              Receive updates on analysis completion
            </div>
          </div>
          <button
            type="button"
            onClick={() => setEmailNotifications((v) => !v)}
            style={{
              width: 44,
              height: 24,
              borderRadius: 12,
              border: "none",
              background: emailNotifications
                ? "var(--accent)"
                : "var(--border)",
              cursor: "pointer",
              position: "relative",
              transition: "background 0.2s",
            }}
          >
            <span
              style={{
                position: "absolute",
                top: 2,
                left: emailNotifications ? 22 : 2,
                width: 20,
                height: 20,
                borderRadius: "50%",
                background: "#fff",
                transition: "left 0.2s",
              }}
            />
          </button>
        </div>
      </div>
    </div>
  );
}
