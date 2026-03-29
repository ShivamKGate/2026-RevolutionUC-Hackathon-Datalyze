// ─── Auth Types ───────────────────────────────────────────────────────────────

export type User = {
  id: number;
  email: string;
  name: string;
  role: string;
  setup_complete: boolean;
  onboarding_path?: string;
  display_name?: string | null;
  job_title?: string | null;
  company_id?: number | null;
  company_name?: string | null;
  public_scrape_enabled?: boolean;
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
  await fetch("/api/v1/auth/logout", {
    method: "POST",
    credentials: "include",
  });
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

export type ProfileUpdateRequest = { name: string; job_title?: string | null };

export async function updateUserProfile(
  body: ProfileUpdateRequest,
): Promise<User> {
  const response = await fetch("/api/v1/users/me/profile", {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    credentials: "include",
    body: JSON.stringify(body),
  });
  if (!response.ok) {
    const detail = await response.text();
    throw new Error(`Profile update failed (${response.status}): ${detail}`);
  }
  return (await response.json()) as User;
}

export async function updateUserCompany(body: {
  company_name: string;
  public_scrape_enabled?: boolean | null;
  onboarding_path?: string | null;
}): Promise<User> {
  const response = await fetch("/api/v1/users/me/company", {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    credentials: "include",
    body: JSON.stringify(body),
  });
  if (!response.ok) {
    const detail = await response.text();
    throw new Error(`Company update failed (${response.status}): ${detail}`);
  }
  return (await response.json()) as User;
}

// ─── Health ───────────────────────────────────────────────────────────────────

export type HealthResponse = {
  status: string;
  service: string;
  timestamp: string;
};

export async function getHealth(): Promise<HealthResponse> {
  const response = await fetch("/api/v1/health", { credentials: "include" });
  if (!response.ok)
    throw new Error(`Health check failed with status ${response.status}`);
  return (await response.json()) as HealthResponse;
}

// ─── Agent MVP ────────────────────────────────────────────────────────────────

export type AgentMVPRequest = {
  company_context: string;
  user_goal: string;
  run: boolean;
};
export type AgentMVPResponse = {
  status: string;
  run_executed: boolean;
  llm_provider: string;
  llm_base_url: string;
  heavy_model: string;
  heavy_alt_model: string;
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
    credentials: "include",
    body: JSON.stringify(body),
  });
  if (!response.ok) {
    const detail = await response.text();
    throw new Error(`Agent MVP request failed (${response.status}): ${detail}`);
  }
  return (await response.json()) as AgentMVPResponse;
}

// ─── Model catalog (Featherless; route name: ollama-catalog) ─────────────────

export type OllamaCatalogResponse = {
  hardware_summary: string;
  defaults: Record<string, string>;
  models: { id: string; tier: string; notes: string }[];
  pull_commands: string[];
  llm_api_key_configured: boolean;
  llm_sanity_message: string;
};

export async function getOllamaCatalog(): Promise<OllamaCatalogResponse> {
  const response = await fetch("/api/v1/agents/ollama-catalog", {
    credentials: "include",
  });
  if (!response.ok)
    throw new Error(`Catalog fetch failed with status ${response.status}`);
  return (await response.json()) as OllamaCatalogResponse;
}

// ─── Database Status ──────────────────────────────────────────────────────────

export type DbTable = { name: string; row_count: number };
export type DbStatusResponse = {
  connected: boolean;
  database?: string;
  tables: DbTable[];
  error?: string;
};

export async function getDbStatus(): Promise<DbStatusResponse> {
  const response = await fetch("/api/v1/database/status", {
    credentials: "include",
  });
  if (!response.ok)
    throw new Error(`DB status check failed with status ${response.status}`);
  return (await response.json()) as DbStatusResponse;
}

// ─── Agent Boot Status ────────────────────────────────────────────────────────

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
  crewai_total: number;
  crewai_initialized: number;
  init_summary: string;
  local_agents: number;
  external_agents: number;
  system_agents: number;
  errors: string[];
  agents: BootAgentNode[];
  orchestrator_policy: { max_retries: number; timeout_seconds: number };
};

export async function getAgentBootStatus(): Promise<AgentBootStatusResponse> {
  const response = await fetch("/api/v1/agents/boot-status", {
    credentials: "include",
  });
  if (!response.ok)
    throw new Error(`Boot status fetch failed with status ${response.status}`);
  return (await response.json()) as AgentBootStatusResponse;
}

// ─── Uploads & pipeline runs ──────────────────────────────────────────────────

export type UploadedFile = {
  id: number;
  original_filename: string;
  byte_size: number;
  visibility: string;
  content_type: string | null;
  created_at: string;
};

export async function uploadDataFile(file: File): Promise<UploadedFile> {
  const body = new FormData();
  body.append("file", file);
  const response = await fetch("/api/v1/files/upload", {
    method: "POST",
    credentials: "include",
    body,
  });
  if (!response.ok) {
    const detail = await response.text();
    throw new Error(`Upload failed (${response.status}): ${detail}`);
  }
  return (await response.json()) as UploadedFile;
}

export async function listUploadedFiles(): Promise<UploadedFile[]> {
  const response = await fetch("/api/v1/files", { credentials: "include" });
  if (!response.ok) throw new Error(`List files failed (${response.status})`);
  return (await response.json()) as UploadedFile[];
}

export async function deleteUploadedFile(id: number): Promise<void> {
  const response = await fetch(`/api/v1/files/${id}`, {
    method: "DELETE",
    credentials: "include",
  });
  if (!response.ok) throw new Error(`Delete failed (${response.status})`);
}

export type AgentActivityRow = {
  agent_id: string;
  agent_name: string;
  status: string;
  message: string;
};

export type PipelineRun = {
  id: number;
  slug: string;
  status: string;
  started_at: string;
  ended_at: string | null;
  summary: string | null;
  pipeline_log: string[];
  agent_activity: AgentActivityRow[];
  source_file_ids: number[];
  track: string | null;
  config_json: Record<string, unknown>;
  final_status_class: string | null;
  replay_payload: Record<string, unknown> | null;
  run_dir_path: string | null;
};

export type PipelineRunLog = {
  id: number;
  timestamp: string | null;
  stage: string;
  agent: string;
  action: string;
  detail: string;
  status: string;
  meta: Record<string, unknown>;
};

export type PipelineRunReplay = {
  run: PipelineRun;
  logs: PipelineRunLog[];
  replay_payload: Record<string, unknown>;
};

export type ClearRunsResponse = {
  status: string;
  deleted_runs: number;
  deleted_run_dirs: number;
  filesystem_errors: string[];
};

export async function listPipelineRuns(): Promise<PipelineRun[]> {
  const response = await fetch("/api/v1/runs", { credentials: "include" });
  if (!response.ok) throw new Error(`List runs failed (${response.status})`);
  return (await response.json()) as PipelineRun[];
}

export async function getPipelineRun(slug: string): Promise<PipelineRun> {
  const response = await fetch(`/api/v1/runs/${encodeURIComponent(slug)}`, {
    credentials: "include",
  });
  if (!response.ok) throw new Error(`Run not found (${response.status})`);
  return (await response.json()) as PipelineRun;
}

export async function getLatestPipelineRun(): Promise<PipelineRun | null> {
  const response = await fetch("/api/v1/runs/latest/summary", {
    credentials: "include",
  });
  if (!response.ok) throw new Error(`Latest run failed (${response.status})`);
  const data: unknown = await response.json();
  if (data == null) return null;
  return data as PipelineRun;
}

export async function startPipelineRun(body: {
  uploaded_file_ids: number[];
}): Promise<PipelineRun> {
  const response = await fetch("/api/v1/runs/start", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    credentials: "include",
    body: JSON.stringify(body),
  });
  if (!response.ok) {
    const detail = await response.text();
    throw new Error(`Start run failed (${response.status}): ${detail}`);
  }
  return (await response.json()) as PipelineRun;
}

export async function getPipelineRunLogs(
  slug: string,
): Promise<PipelineRunLog[]> {
  const response = await fetch(
    `/api/v1/runs/${encodeURIComponent(slug)}/logs`,
    {
      credentials: "include",
    },
  );
  if (!response.ok) throw new Error(`Run logs failed (${response.status})`);
  return (await response.json()) as PipelineRunLog[];
}

export async function getPipelineRunReplay(
  slug: string,
): Promise<PipelineRunReplay> {
  const response = await fetch(
    `/api/v1/runs/${encodeURIComponent(slug)}/replay`,
    {
      credentials: "include",
    },
  );
  if (!response.ok) throw new Error(`Run replay failed (${response.status})`);
  return (await response.json()) as PipelineRunReplay;
}

export async function clearAllPipelineRuns(): Promise<ClearRunsResponse> {
  const response = await fetch("/api/v1/runs", {
    method: "DELETE",
    credentials: "include",
  });
  if (!response.ok) {
    const detail = await response.text();
    throw new Error(`Clear analyses failed (${response.status}): ${detail}`);
  }
  return (await response.json()) as ClearRunsResponse;
}
