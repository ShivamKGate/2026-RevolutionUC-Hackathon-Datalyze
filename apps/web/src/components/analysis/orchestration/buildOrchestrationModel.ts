import type { AgentActivityRow, PipelineRunLog } from "../../../lib/api";
import type { AgentResults } from "../types";

export type OrchNodeKind =
  | "orchestrator"
  | "agent"
  | "data"
  | "kg_hub"
  | "insight";

export type OrchNode = {
  id: string;
  label: string;
  kind: OrchNodeKind;
  status?: string;
  message?: string;
  sourceType?: string;
  /** Raw agent_id when kind is agent */
  agentKey?: string;
  /** For insight nodes — index into insight_generation.insights */
  insightIndex?: number;
};

export type OrchEdge = {
  from: string;
  to: string;
  kind?: "core" | "kg" | "insight_flow" | "provenance";
};

const KG_HUB_ID = "kg:hub";

/** First-seen dispatch order per agent (0 = earliest). Parallel batch order follows log order. */
export function buildDispatchOrderMap(
  logs: PipelineRunLog[],
): Record<string, number> {
  const out: Record<string, number> = {};
  let seq = 0;
  for (const l of logs) {
    const act = (l.action || "").trim().toLowerCase();
    if (act !== "dispatch") continue;
    const agent = (l.agent || "").trim();
    if (!agent || agent.toLowerCase() === "orchestrator") continue;
    if (out[agent] !== undefined) continue;
    out[agent] = seq;
    seq += 1;
  }
  return out;
}

/**
 * DAG + KG hub + insight satellites for the 3D orchestration view.
 * @param liveDispatchLogs When set (e.g. while a run is active), agents seen in dispatch log lines
 *   are added immediately so the graph updates before `agent_activity` catches up.
 */
export function buildOrchestrationModel(
  agentActivity: AgentActivityRow[],
  agentResults: AgentResults,
  track: string | null,
  sourceFileCount: number,
  liveDispatchLogs?: PipelineRunLog[] | null,
): { nodes: OrchNode[]; edges: OrchEdge[] } {
  const nodes: OrchNode[] = [];
  const edges: OrchEdge[] = [];
  const rootId = "orchestrator";

  nodes.push({
    id: rootId,
    label: "Orchestrator",
    kind: "orchestrator",
    status: "coordinating",
    message: track ? `Track: ${track.replace(/_/g, " ")}` : "Pipeline",
    sourceType: "core",
  });

  const seen = new Set<string>();
  for (const row of agentActivity) {
    if (!row.agent_id || seen.has(row.agent_id)) continue;
    seen.add(row.agent_id);
    const id = `agent:${row.agent_id}`;
    nodes.push({
      id,
      label: row.agent_name || row.agent_id.replace(/_/g, " "),
      kind: "agent",
      status: row.status,
      message: row.message,
      sourceType: "agent",
      agentKey: row.agent_id,
    });
    edges.push({ from: rootId, to: id, kind: "core" });
  }

  for (const key of Object.keys(agentResults)) {
    if (seen.has(key)) continue;
    seen.add(key);
    const id = `agent:${key}`;
    nodes.push({
      id,
      label: key.replace(/_/g, " "),
      kind: "agent",
      status: "completed",
      message: "Output available",
      sourceType: "agent",
      agentKey: key,
    });
    edges.push({ from: rootId, to: id, kind: "core" });
  }

  if (liveDispatchLogs?.length) {
    const dispatchOrder = buildDispatchOrderMap(liveDispatchLogs);
    const orderedAgentIds = Object.entries(dispatchOrder)
      .sort((a, b) => a[1] - b[1])
      .map(([id]) => id);
    for (const agentId of orderedAgentIds) {
      if (seen.has(agentId)) continue;
      seen.add(agentId);
      const id = `agent:${agentId}`;
      nodes.push({
        id,
        label: agentId.replace(/_/g, " "),
        kind: "agent",
        status: "running",
        message: "Dispatched (from live log)",
        sourceType: "agent",
        agentKey: agentId,
      });
      edges.push({ from: rootId, to: id, kind: "core" });
    }
  }

  if (sourceFileCount > 0) {
    const id = "data:uploads";
    nodes.push({
      id,
      label: "User uploads",
      kind: "data",
      sourceType: "upload",
      message: `${sourceFileCount} file(s)`,
    });
    edges.push({ from: rootId, to: id, kind: "core" });
  }

  nodes.push({
    id: "data:public",
    label: "Public / web sources",
    kind: "data",
    sourceType: "public_scrape",
    message: "Enrichment & crawl",
  });
  edges.push({ from: rootId, to: "data:public", kind: "core" });

  nodes.push({
    id: "data:internet",
    label: "Internet aggregation",
    kind: "data",
    sourceType: "internet",
    message: "LLM + retrieval",
  });
  edges.push({ from: rootId, to: "data:internet", kind: "core" });

  const kg = agentResults.knowledge_graph_builder;
  const kgNodeCount = kg?.nodes?.length ?? 0;
  if (kgNodeCount > 0) {
    nodes.push({
      id: KG_HUB_ID,
      label: "Knowledge graph",
      kind: "kg_hub",
      sourceType: "knowledge_graph",
      message: `${kgNodeCount} nodes · ${(kg?.edges ?? []).length} edges`,
    });
    const kgBuilderId = "agent:knowledge_graph_builder";
    if (nodes.some((n) => n.id === kgBuilderId)) {
      edges.push({ from: kgBuilderId, to: KG_HUB_ID, kind: "kg" });
    } else {
      edges.push({ from: rootId, to: KG_HUB_ID, kind: "kg" });
    }
    const contributors = [
      "trend_forecasting",
      "insight_generation",
      "aggregator",
      "conflict_detection",
    ];
    for (const aid of contributors) {
      const nid = `agent:${aid}`;
      if (nodes.some((n) => n.id === nid)) {
        edges.push({ from: nid, to: KG_HUB_ID, kind: "provenance" });
      }
    }
  }

  const rawInsights = agentResults.insight_generation?.insights;
  const insights = Array.isArray(rawInsights) ? rawInsights : [];
  const igId = "agent:insight_generation";
  insights.forEach((ins, i) => {
    const id = `insight:${i}`;
    const title = ins.title?.slice(0, 42) || `Insight ${i + 1}`;
    nodes.push({
      id,
      label: title,
      kind: "insight",
      sourceType: "insight",
      message: ins.description?.slice(0, 200),
      insightIndex: i,
    });
    if (nodes.some((n) => n.id === igId)) {
      edges.push({ from: igId, to: id, kind: "insight_flow" });
    } else {
      edges.push({ from: rootId, to: id, kind: "insight_flow" });
    }
    if (kgNodeCount > 0) {
      edges.push({ from: id, to: KG_HUB_ID, kind: "insight_flow" });
    }
  });

  return { nodes, edges };
}

export function logAgentToNodeId(agentField: string): string | null {
  const a = (agentField || "").trim();
  if (!a || a === "—") return null;
  return `agent:${a}`;
}

export function agentRolePercent(
  agentKey: string,
  logs: PipelineRunLog[],
): number {
  if (!logs.length) return 0;
  const n = logs.filter((l) => (l.agent || "").trim() === agentKey).length;
  return Math.round((100 * n) / logs.length);
}
