import { useState, type FormEvent } from "react";
import { useAuth } from "../../contexts/AuthContext";

export default function ProfilePage() {
  const { user } = useAuth();
  const [displayName, setDisplayName] = useState(user?.name ?? "");
  const [jobTitle, setJobTitle] = useState("");
  const [saved, setSaved] = useState(false);

  function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
  }

  return (
    <div>
      <h2 style={{ marginTop: 0 }}>Profile</h2>
      <form onSubmit={handleSubmit} style={{ maxWidth: 400, display: "flex", flexDirection: "column", gap: "1.25rem" }}>
        <div className="form-group">
          <label className="form-label" htmlFor="profile-name">Display Name</label>
          <input
            id="profile-name"
            type="text"
            className="form-input"
            value={displayName}
            onChange={(e) => setDisplayName(e.target.value)}
          />
        </div>
        <div className="form-group">
          <label className="form-label" htmlFor="profile-email">Email</label>
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
          <label className="form-label" htmlFor="profile-title">Job Title</label>
          <input
            id="profile-title"
            type="text"
            className="form-input"
            value={jobTitle}
            onChange={(e) => setJobTitle(e.target.value)}
            placeholder="e.g. Data Analyst"
          />
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: "1rem" }}>
          <button type="submit" className="btn-primary">Save Changes</button>
          {saved && <span style={{ color: "#4ade80", fontSize: "0.875rem" }}>Saved!</span>}
        </div>
      </form>
    </div>
  );
}
