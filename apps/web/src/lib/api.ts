// ─── Auth Types ───────────────────────────────────────────────────────────────

export type User = {
  id: number;
  email: string;
  name: string;
  role: string;
  setup_complete: boolean;
  onboarding_path?: string;
};

export type LoginRequest = { email: string; password: string };
export type SignupRequest = { name: string; email: string; password: string };
export type SetupRequest = {
  company_name: string;
  display_name?: string;
  job_title?: string;
  onboarding_path: string;
};

// ─── Auth Endpoints ───────────────────────────────────────────────────────────

export async function authMe(): Promise<User> {
  const response = await fetch("/api/v1/auth/me", { credentials: "include" });
  if (!response.ok) throw new Error(`Not authenticated (${response.status})`);
  return (await response.json()) as User;
}

export async function authLogin(body: LoginRequest): Promise<User> {
  const response = await fetch("/api/v1/auth/login", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    credentials: "include",
    body: JSON.stringify(body),
  });
  if (!response.ok) {
    const detail = await response.text();
    throw new Error(`Login failed (${response.status}): ${detail}`);
  }
  return (await response.json()) as User;
}

export async function authSignup(body: SignupRequest): Promise<User> {
  const response = await fetch("/api/v1/auth/register", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    credentials: "include",
    body: JSON.stringify(body),
  });
  if (!response.ok) {
    const detail = await response.text();
    throw new Error(`Sign up failed (${response.status}): ${detail}`);
  }
  return (await response.json()) as User;
}

export async function authLogout(): Promise<void> {
  await fetch("/api/v1/auth/logout", { method: "POST", credentials: "include" });
}

export async function setupUser(body: SetupRequest): Promise<User> {
  const response = await fetch("/api/v1/users/me/setup", {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    credentials: "include",
    body: JSON.stringify(body),
  });
  if (!response.ok) {
    const detail = await response.text();
    throw new Error(`Setup failed (${response.status}): ${detail}`);
  }
  return (await response.json()) as User;
}

// ─── Health ───────────────────────────────────────────────────────────────────

export type HealthResponse = { status: string; service: string; timestamp: string };

export async function getHealth(): Promise<HealthResponse> {
  const response = await fetch("/api/v1/health", { credentials: "include" });
  if (!response.ok) throw new Error(`Health check failed with status ${response.status}`);
  return (await response.json()) as HealthResponse;
}

// ─── Agent MVP ────────────────────────────────────────────────────────────────

export type AgentMVPRequest = { company_context: string; user_goal: string; run: boolean };
export type AgentMVPResponse = {
  status: string; run_executed: boolean; ollama_host: string;
  heavy_model: string; light_model: string; embedding_model: string;
  agents_initialized: string[]; tasks_initialized: number; output: string | null;
};

export async function postAgentsMVP(body: AgentMVPRequest): Promise<AgentMVPResponse> {
  const response = await fetch("/api/v1/agents/mvp", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    credentials: "include",
    body: JSON.stringify(body),
  });
  if (!response.ok) {
    const detail = await response.text();
    throw new Error(`Agent MVP request failed (${response.status}): ${detail}`);
  }
  return (await response.json()) as AgentMVPResponse;
}

// ─── Ollama Catalog ───────────────────────────────────────────────────────────

export type OllamaCatalogResponse = {
  hardware_summary: string;
  defaults: Record<string, string>;
  models: { id: string; tier: string; notes: string }[];
  pull_commands: string[];
};

export async function getOllamaCatalog(): Promise<OllamaCatalogResponse> {
  const response = await fetch("/api/v1/agents/ollama-catalog", { credentials: "include" });
  if (!response.ok) throw new Error(`Catalog fetch failed with status ${response.status}`);
  return (await response.json()) as OllamaCatalogResponse;
}

// ─── Database Status ──────────────────────────────────────────────────────────

export type DbTable = { name: string; row_count: number };
export type DbStatusResponse = { connected: boolean; database?: string; tables: DbTable[]; error?: string };

export async function getDbStatus(): Promise<DbStatusResponse> {
  const response = await fetch("/api/v1/database/status", { credentials: "include" });
  if (!response.ok) throw new Error(`DB status check failed with status ${response.status}`);
  return (await response.json()) as DbStatusResponse;
}

// ─── Agent Boot Status ────────────────────────────────────────────────────────

export type BootAgentNode = {
  id: string; name: string; model_type: string; model_resolved: string;
  runtime_kind: string; priority: string; dependencies: string[];
  dependencies_resolved: boolean; initialized: boolean;
};
export type AgentBootStatusResponse = {
  status: string; booted_at: string | null; total_agents: number;
  initialized_agents: number; local_agents: number; external_agents: number;
  system_agents: number; errors: string[]; agents: BootAgentNode[];
  orchestrator_policy: { max_retries: number; timeout_seconds: number };
};

export async function getAgentBootStatus(): Promise<AgentBootStatusResponse> {
  const response = await fetch("/api/v1/agents/boot-status", { credentials: "include" });
  if (!response.ok) throw new Error(`Boot status fetch failed with status ${response.status}`);
  return (await response.json()) as AgentBootStatusResponse;
}
