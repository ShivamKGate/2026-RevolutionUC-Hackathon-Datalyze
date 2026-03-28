import { useState } from "react";

import {
  getAgentBootStatus,
  getHealth,
  getOllamaCatalog,
  postAgentsMVP,
  type AgentBootStatusResponse,
  type AgentMVPResponse,
  type HealthResponse,
  type OllamaCatalogResponse,
} from "./lib/api";

export default function App() {
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [catalog, setCatalog] = useState<OllamaCatalogResponse | null>(null);
  const [bootStatus, setBootStatus] = useState<AgentBootStatusResponse | null>(null);
  const [agentResult, setAgentResult] = useState<AgentMVPResponse | null>(null);
  const [loading, setLoading] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function runHealthCheck() {
    setLoading("health");
    setError(null);
    try {
      setHealth(await getHealth());
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unexpected error");
      setHealth(null);
    } finally {
      setLoading(null);
    }
  }

  async function fetchCatalog() {
    setLoading("catalog");
    setError(null);
    try {
      setCatalog(await getOllamaCatalog());
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unexpected error");
      setCatalog(null);
    } finally {
      setLoading(null);
    }
  }

  async function initAgents() {
    setLoading("agents");
    setError(null);
    try {
      const mvp = await postAgentsMVP({
        company_context:
          "Small business with mixed sales and operations files.",
        user_goal: "Find key business risks and top growth opportunities.",
        run: false,
      });
      setAgentResult(mvp);
      setBootStatus(
        await getAgentBootStatus(),
      );
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unexpected error");
      setAgentResult(null);
    } finally {
      setLoading(null);
    }
  }

  async function fetchBootStatus() {
    setLoading("boot");
    setError(null);
    try {
      setBootStatus(await getAgentBootStatus());
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unexpected error");
      setBootStatus(null);
    } finally {
      setLoading(null);
    }
  }

  return (
    <main className="page">
      <section className="panel">
        <h1>Datalyze</h1>
        <p>Raw Data down, AI-Driven Strategies up.</p>

        <div className="button-row">
          <button onClick={runHealthCheck} disabled={loading !== null}>
            {loading === "health" ? "Checking..." : "Check API"}
          </button>
          <button onClick={fetchCatalog} disabled={loading !== null}>
            {loading === "catalog" ? "Loading..." : "Ollama Catalog"}
          </button>
          <button onClick={fetchBootStatus} disabled={loading !== null}>
            {loading === "boot" ? "Loading..." : "Boot Status"}
          </button>
          <button onClick={initAgents} disabled={loading !== null}>
            {loading === "agents" ? "Initializing..." : "Init Agents"}
          </button>
        </div>

        {error && (
          <div className="status error">
            <strong>Error:</strong> {error}
          </div>
        )}

        {health && (
          <div className="status success">
            <strong>API:</strong> {health.service} ({health.status}) at{" "}
            {health.timestamp}
          </div>
        )}

        {catalog && (
          <div className="status success">
            <strong>Hardware:</strong> {catalog.hardware_summary}
            <div className="detail-grid">
              {catalog.models.map((m) => (
                <div key={m.id} className="detail-card">
                  <code>{m.id}</code>
                  <span className="badge">{m.tier}</span>
                  <p>{m.notes}</p>
                </div>
              ))}
            </div>
          </div>
        )}

        {agentResult && (
          <div className="status success">
            <strong>Agents initialized (registry):</strong>
            <ul>
              {agentResult.agents_initialized.map((name) => (
                <li key={name}>{name}</li>
              ))}
            </ul>
            <p>
              MVP tasks: {agentResult.tasks_initialized} | Heavy:{" "}
              <code>{agentResult.heavy_model}</code> | Light:{" "}
              <code>{agentResult.light_model}</code>
            </p>
            {agentResult.output && (
              <pre className="output-block">{agentResult.output}</pre>
            )}
          </div>
        )}

        {bootStatus && (
          <div className="status success">
            <strong>Registry:</strong> {bootStatus.status} | initialized{" "}
            {bootStatus.initialized_agents}/{bootStatus.total_agents}
            <p>
              Local: {bootStatus.local_agents} | External: {bootStatus.external_agents} |
              System: {bootStatus.system_agents}
            </p>
            <p>
              Orchestrator policy: retries {bootStatus.orchestrator_policy.max_retries},
              timeout {bootStatus.orchestrator_policy.timeout_seconds}s
            </p>
            <div className="scroll-list">
              {bootStatus.agents.map((node) => (
                <div className="detail-card" key={node.id}>
                  <code>{node.name}</code>
                  <span className="badge">{node.model_type}</span>
                  <p>
                    {node.runtime_kind} | model {node.model_resolved} | deps{" "}
                    {node.dependencies.length}
                  </p>
                </div>
              ))}
            </div>
          </div>
        )}
      </section>
    </main>
  );
}
