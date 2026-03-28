import { useEffect, useState, type FormEvent } from "react";
import { useAuth } from "../../contexts/AuthContext";
import { updateUserProfile } from "../../lib/api";

export default function ProfilePage() {
  const { user, refreshUser } = useAuth();
  const [displayName, setDisplayName] = useState("");
  const [jobTitle, setJobTitle] = useState("");
  const [saved, setSaved] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!user) return;
    const shown =
      user.display_name && user.display_name.trim().length > 0
        ? user.display_name
        : user.name;
    setDisplayName(shown);
    setJobTitle(user.job_title ?? "");
  }, [user]);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    const name = displayName.trim();
    if (!name) {
      setError("Display name is required.");
      return;
    }
    setSaving(true);
    setError(null);
    setSaved(false);
    try {
      await updateUserProfile({
        name,
        job_title: jobTitle.trim() ? jobTitle.trim() : null,
      });
      await refreshUser();
      setSaved(true);
      setTimeout(() => setSaved(false), 2000);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Save failed");
    } finally {
      setSaving(false);
    }
  }

  return (
    <div>
      <h2 style={{ marginTop: 0 }}>Profile</h2>
      <form
        onSubmit={handleSubmit}
        style={{
          maxWidth: 400,
          display: "flex",
          flexDirection: "column",
          gap: "1.25rem",
        }}
      >
        {error && (
          <div
            className="status error"
            style={{ margin: 0, padding: "0.6rem 0.75rem", borderRadius: 6 }}
          >
            {error}
          </div>
        )}
        <div className="form-group">
          <label className="form-label" htmlFor="profile-name">
            Display Name
          </label>
          <input
            id="profile-name"
            type="text"
            className="form-input"
            value={displayName}
            onChange={(e) => setDisplayName(e.target.value)}
            required
          />
        </div>
        <div className="form-group">
          <label className="form-label" htmlFor="profile-email">
            Email
          </label>
          <input
            id="profile-email"
            type="email"
            className="form-input"
            value={user?.email ?? ""}
            readOnly
            style={{ opacity: 0.6, cursor: "not-allowed" }}
          />
        </div>
        <div className="form-group">
          <label className="form-label" htmlFor="profile-title">
            Job Title
          </label>
          <input
            id="profile-title"
            type="text"
            className="form-input"
            value={jobTitle}
            onChange={(e) => setJobTitle(e.target.value)}
            placeholder="e.g. Data Analyst"
          />
        </div>
        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: "1rem",
            flexWrap: "wrap",
          }}
        >
          <button type="submit" className="btn-primary" disabled={saving}>
            {saving ? "Saving…" : "Save Changes"}
          </button>
          {saved && (
            <span style={{ color: "#4ade80", fontSize: "0.875rem" }}>
              Saved!
            </span>
          )}
        </div>
      </form>
    </div>
  );
}
