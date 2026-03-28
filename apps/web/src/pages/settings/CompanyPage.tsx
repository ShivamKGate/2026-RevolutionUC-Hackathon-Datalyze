import { useState, type FormEvent } from "react";

export default function CompanyPage() {
  const [companyName, setCompanyName] = useState("");
  const [saved, setSaved] = useState(false);

  function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
  }

  return (
    <div>
      <h2 style={{ marginTop: 0 }}>Company</h2>
      <form onSubmit={handleSubmit} style={{ maxWidth: 400, display: "flex", flexDirection: "column", gap: "1.25rem" }}>
        <div className="form-group">
          <label className="form-label" htmlFor="company-name">Company Name</label>
          <input
            id="company-name"
            type="text"
            className="form-input"
            value={companyName}
            onChange={(e) => setCompanyName(e.target.value)}
            placeholder="Acme Corp"
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
