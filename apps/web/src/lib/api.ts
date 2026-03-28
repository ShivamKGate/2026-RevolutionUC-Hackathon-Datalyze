export type HealthResponse = {
  status: string;
  service: string;
  timestamp: string;
};

export async function getHealth(): Promise<HealthResponse> {
  const response = await fetch("/api/v1/health");

  if (!response.ok) {
    throw new Error(`Health check failed with status ${response.status}`);
  }

  return (await response.json()) as HealthResponse;
}

export type AgentMVPRequest = {
  company_context: string;
  user_goal: string;
  run: boolean;
};

export type AgentMVPResponse = {
  status: string;
  run_executed: boolean;
  ollama_host: string;
  heavy_model: string;
  light_model: string;
  embedding_model: string;
  agents_initialized: string[];
  tasks_initialized: number;
  output: string | null;
};

export async function postAgentsMVP(
  body: AgentMVPRequest,
): Promise<AgentMVPResponse> {
  const response = await fetch("/api/v1/agents/mvp", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });

  if (!response.ok) {
    const detail = await response.text();
    throw new Error(`Agent MVP request failed (${response.status}): ${detail}`);
  }

  return (await response.json()) as AgentMVPResponse;
}

export type OllamaCatalogResponse = {
  hardware_summary: string;
  defaults: Record<string, string>;
  models: { id: string; tier: string; notes: string }[];
  pull_commands: string[];
};

export async function getOllamaCatalog(): Promise<OllamaCatalogResponse> {
  const response = await fetch("/api/v1/agents/ollama-catalog");

  if (!response.ok) {
    throw new Error(`Catalog fetch failed with status ${response.status}`);
  }

  return (await response.json()) as OllamaCatalogResponse;
}
