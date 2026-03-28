import { useState } from "react";

import { getHealth, type HealthResponse } from "./lib/api";

export default function App() {
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function runHealthCheck() {
    setLoading(true);
    setError(null);

    try {
      const result = await getHealth();
      setHealth(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unexpected error");
      setHealth(null);
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="page">
      <section className="panel">
        <h1>Datalyze</h1>
        <p>Raw Data down, AI-Driven Strategies up.</p>
        <button onClick={runHealthCheck} disabled={loading}>
          {loading ? "Checking..." : "Check API Connection"}
        </button>

        {health && (
          <div className="status success">
            <strong>Connected:</strong> {health.service} ({health.status}) at{" "}
            {health.timestamp}
          </div>
        )}

        {error && (
          <div className="status error">
            <strong>Connection error:</strong> {error}
          </div>
        )}
      </section>
    </main>
  );
}
