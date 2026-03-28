import { useState, type FormEvent } from "react";
import { useNavigate } from "react-router-dom";
import { setupUser } from "../lib/api";
import { useAuth } from "../contexts/AuthContext";

const PATHS = [
  { id: "devops", label: "DevOps / Automations", description: "Optimize pipelines and automate workflows" },
  { id: "automations", label: "Business Automations", description: "Streamline repetitive processes" },
  { id: "deep_analysis", label: "Deep Analysis", description: "In-depth data exploration and reporting" },
];

export default function SetupPage() {
  const { refreshUser } = useAuth();
  const navigate = useNavigate();
  const [companyName, setCompanyName] = useState("");
  const [jobTitle, setJobTitle] = useState("");
  const [selectedPath, setSelectedPath] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    if (!selectedPath) {
      setError("Please select a usage path.");
      return;
    }
    setLoading(true);
    setError(null);
    try {
      await setupUser({
        company_name: companyName,
        job_title: jobTitle || undefined,
        onboarding_path: selectedPath,
      });
      await refreshUser();
      navigate("/dashboard");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Setup failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div style={{ maxWidth: 560, margin: "4rem auto", padding: "0 1rem" }}>
      <h1 style={{ marginTop: 0 }}>Set Up Your Account</h1>
      <p style={{ color: "var(--text-muted)", marginBottom: "2rem" }}>
        Tell us a bit about yourself so we can tailor the experience.
      </p>
      <form onSubmit={handleSubmit}>
        <div style={{ display: "flex", flexDirection: "column", gap: "1.25rem" }}>
          {error && (
            <div className="status error" style={{ margin: 0, padding: "0.6rem 0.75rem", borderRadius: 6 }}>
              {error}
            </div>
          )}
          <div className="form-group">
            <label className="form-label" htmlFor="setup-company">Company Name</label>
            <input
              id="setup-company"
              type="text"
              className="form-input"
              value={companyName}
              onChange={(e) => setCompanyName(e.target.value)}
              required
              placeholder="Acme Corp"
            />
          </div>
          <div className="form-group">
            <label className="form-label" htmlFor="setup-title">Job Title (optional)</label>
            <input
              id="setup-title"
              type="text"
              className="form-input"
              value={jobTitle}
              onChange={(e) => setJobTitle(e.target.value)}
              placeholder="e.g. Data Analyst"
            />
          </div>
          <div className="form-group">
            <label className="form-label">How will you primarily use Datalyze?</label>
            <div className="usage-path-grid">
              {PATHS.map((p) => (
                <button
                  key={p.id}
                  type="button"
                  className={"usage-path-card" + (selectedPath === p.id ? " selected" : "")}
                  onClick={() => setSelectedPath(p.id)}
                >
                  <strong>{p.label}</strong>
                  <span>{p.description}</span>
                </button>
              ))}
            </div>
          </div>
          <button
            type="submit"
            className="btn-primary"
            disabled={loading}
            style={{ alignSelf: "flex-start", padding: "0.65rem 2rem" }}
          >
            {loading ? "Saving..." : "Continue to Dashboard"}
          </button>
        </div>
      </form>
    </div>
  );
}
