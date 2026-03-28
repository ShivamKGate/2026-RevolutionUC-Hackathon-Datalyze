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

export type DbTable = {
  name: string;
  row_count: number;
};

export type DbStatusResponse = {
  connected: boolean;
  database?: string;
  tables: DbTable[];
  error?: string;
};

export async function getDbStatus(): Promise<DbStatusResponse> {
  const response = await fetch("/api/v1/database/status");

  if (!response.ok) {
    throw new Error(`DB status check failed with status ${response.status}`);
  }

  return (await response.json()) as DbStatusResponse;
}

export type BootAgentNode = {
  id: string;
  name: string;
  model_type: string;
  model_resolved: string;
  runtime_kind: string;
  priority: string;
  dependencies: string[];
  dependencies_resolved: boolean;
  initialized: boolean;
};

export type AgentBootStatusResponse = {
  status: string;
  booted_at: string | null;
  total_agents: number;
  initialized_agents: number;
  local_agents: number;
  external_agents: number;
  system_agents: number;
  errors: string[];
  agents: BootAgentNode[];
  orchestrator_policy: { max_retries: number; timeout_seconds: number };
};

export async function getAgentBootStatus(): Promise<AgentBootStatusResponse> {
  const response = await fetch("/api/v1/agents/boot-status");

  if (!response.ok) {
    throw new Error(`Boot status fetch failed with status ${response.status}`);
  }

  return (await response.json()) as AgentBootStatusResponse;
}
