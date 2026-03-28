import { useEffect, useState, type FormEvent } from "react";
import { useAuth } from "../../contexts/AuthContext";
import { updateUserCompany } from "../../lib/api";

export default function CompanyPage() {
  const { user, refreshUser } = useAuth();
  const [companyName, setCompanyName] = useState("");
  const [publicScrape, setPublicScrape] = useState(false);
  const [saved, setSaved] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!user) return;
    setCompanyName(user.company_name ?? "");
    setPublicScrape(Boolean(user.public_scrape_enabled));
  }, [user]);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    const name = companyName.trim();
    if (!name) {
      setError("Company name is required.");
      return;
    }
    setSaving(true);
    setError(null);
    setSaved(false);
    try {
      await updateUserCompany({
        company_name: name,
        public_scrape_enabled: publicScrape,
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
      <h2 style={{ marginTop: 0 }}>Company</h2>
      <form
        onSubmit={handleSubmit}
        style={{
          maxWidth: 480,
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
          <label className="form-label" htmlFor="company-name">
            Company Name
          </label>
          <input
            id="company-name"
            type="text"
            className="form-input"
            value={companyName}
            onChange={(e) => setCompanyName(e.target.value)}
            placeholder="Google"
            required
          />
        </div>

        <div className="form-group company-toggle-row">
          <label className="form-label" htmlFor="public-scrape">
            Transcrape public data
          </label>
          <div className="toggle-wrap">
            <input
              id="public-scrape"
              type="checkbox"
              className="toggle-input"
              checked={publicScrape}
              onChange={(e) => setPublicScrape(e.target.checked)}
            />
            <span className="toggle-hint">
              When on, you can start an analysis from the dashboard without
              uploading files (placeholder pipeline). Uploads are still saved
              under{" "}
              <code className="inline-code">
                data/company/&lt;name&gt;/private
              </code>
              .
            </span>
          </div>
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
