import type { AgentActivityRow, PipelineRun } from "./api";

/**
 * Coerce API/JSONB quirks so the analysis page never throws on .join / .map.
 * Some runs may deserialize with missing shapes after DB round-trips.
 */
export function normalizePipelineLogLines(value: unknown): string[] {
  if (Array.isArray(value)) {
    return value.map((x) => (typeof x === "string" ? x : String(x ?? "")));
  }
  return [];
}

export function normalizeAgentActivity(value: unknown): AgentActivityRow[] {
  if (!Array.isArray(value)) return [];
  return value
    .filter((x) => x != null && typeof x === "object")
    .map((x) => {
      const r = x as Record<string, unknown>;
      return {
        agent_id: String(r.agent_id ?? ""),
        agent_name: String(r.agent_name ?? r.agent_id ?? "Agent"),
        status: String(r.status ?? "—"),
        message:
          typeof r.message === "string" ? r.message : String(r.message ?? ""),
      };
    });
}

export function normalizeRunForView(run: PipelineRun): PipelineRun {
  return {
    ...run,
    pipeline_log: normalizePipelineLogLines(run.pipeline_log),
    agent_activity: normalizeAgentActivity(run.agent_activity),
  };
}
