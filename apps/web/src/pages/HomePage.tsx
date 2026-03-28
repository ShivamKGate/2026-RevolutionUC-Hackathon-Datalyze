import { useOutletContext } from "react-router-dom";

type OutletCtx = { onLoginOpen: () => void; onSignupOpen: () => void };

export default function HomePage() {
  const { onSignupOpen } = useOutletContext<OutletCtx>();

  return (
    <>
      <section className="hero-section">
        <h1 className="hero-title">Datalyze</h1>
        <p className="hero-tagline">Raw Data ↓, AI-Driven Strategies ↑</p>
        <p className="hero-description">
          Upload your business data and let our AI agents surface risks, opportunities,
          and actionable strategies — all without leaving your browser.
        </p>
        <div className="hero-cta">
          <button className="btn-primary" onClick={onSignupOpen}>Get Started</button>
          <a href="#features" className="btn-secondary">Learn More</a>
        </div>
      </section>

      <section className="features-section" id="features">
        <h2>Everything you need to turn data into decisions</h2>
        <div className="feature-grid">
          <div className="feature-card">
            <h3>Upload &amp; Analyze</h3>
            <p>
              Drop in CSV, Excel, JSON, or PDF files. Datalyze ingests and
              structures your data automatically.
            </p>
          </div>
          <div className="feature-card">
            <h3>AI-Powered Insights</h3>
            <p>
              A coordinated team of AI agents digs through your data to find
              patterns, anomalies, and trends.
            </p>
          </div>
          <div className="feature-card">
            <h3>Actionable Strategies</h3>
            <p>
              Get clear, prioritized recommendations you can act on immediately —
              no data science degree required.
            </p>
          </div>
        </div>
      </section>
    </>
  );
}
