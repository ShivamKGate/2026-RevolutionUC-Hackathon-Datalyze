import { useMemo, useState } from "react";
import type { PipelineRun, PipelineRunLog } from "../../../lib/api";
import type { AgentResults } from "../types";
import { CollapsibleAnalysisSection } from "../shared/CollapsibleAnalysisSection";
import { OrchestrationGraph3D } from "./OrchestrationGraph3D";
import {
  agentRolePercent,
  buildDispatchOrderMap,
  buildOrchestrationModel,
  logAgentToNodeId,
  type OrchNode,
} from "./buildOrchestrationModel";

type FinalReportFrag = {
  agent_summaries?: Record<string, string>;
  completed_agents?: string[];
};

type Props = {
  run: PipelineRun;
  logs: PipelineRunLog[];
  agentResults: AgentResults;
  storagePrefix: string;
  /** Omit outer CollapsibleAnalysisSection (e.g. when wrapped in StatusPanel). */
  embedded?: boolean;
  /**
   * In-flight analysis: same graph + drawer + scrubber as post-run, with live-safe
   * canvas remounting and no ambient rotation.
   */
  live?: boolean;
};

function NodeDetailPanel({
  node,
  run,
  logs,
  agentResults,
  onClose,
}: {
  node: OrchNode;
  run: PipelineRun;
  logs: PipelineRunLog[];
  agentResults: AgentResults;
  onClose: () => void;
}) {
  const rp = run.replay_payload ?? {};
  const fr = rp.final_report as FinalReportFrag | undefined;
  const summaries = fr?.agent_summaries ?? {};
  const completed = fr?.completed_agents ?? [];

  const agentKey =
    node.agentKey ??
    (node.id.startsWith("agent:") ? node.id.slice("agent:".length) : "");

  const activityForAgent = useMemo(() => {
    if (!agentKey) return [];
    return run.agent_activity.filter((a) => a.agent_id === agentKey);
  }, [run.agent_activity, agentKey]);

  const logsForAgent = useMemo(() => {
    if (!agentKey) return [];
    return logs.filter((l) => (l.agent || "").trim() === agentKey);
  }, [logs, agentKey]);

  const rolePct = agentKey ? agentRolePercent(agentKey, logs) : 0;

  const idxInPipeline = agentKey
    ? completed.findIndex((a) => a === agentKey) + 1
    : 0;

  const insightDetail =
    node.kind === "insight" && node.insightIndex != null
      ? agentResults.insight_generation?.insights?.[node.insightIndex]
      : undefined;

  const kg = agentResults.knowledge_graph_builder;

  return (
    <aside className="orch-detail-drawer" aria-label="Node details">
      <div className="orch-detail-drawer-header">
        <h4>{node.label}</h4>
        <button
          type="button"
          className="orch-detail-close nav-btn nav-btn-ghost"
          onClick={onClose}
          aria-label="Close details"
        >
          ✕
        </button>
      </div>
      <div className="orch-detail-drawer-body">
        <div className="orch-graph-detail-row">
          <strong>Type</strong>
          <span>{node.kind.replace("_", " ")}</span>
        </div>

        {node.kind === "agent" && agentKey && (
          <>
            <div className="orch-graph-detail-row">
              <strong>Pipeline role</strong>
              <span>
                ~{rolePct}% of structured log lines · step{" "}
                {idxInPipeline > 0
                  ? `${idxInPipeline}/${completed.length || "?"}`
                  : "—"}{" "}
                in completion order
              </span>
            </div>
            {summaries[agentKey] && (
              <div className="orch-detail-block">
                <strong>Agent output summary</strong>
                <p className="orch-detail-text">{summaries[agentKey]}</p>
              </div>
            )}
            {activityForAgent.length > 0 && (
              <div className="orch-detail-block">
                <strong>Agent activity (live)</strong>
                <ul className="orch-detail-list">
                  {activityForAgent.map((a, i) => (
                    <li key={`${a.agent_id}-${i}`}>
                      <span className="orch-detail-status">{a.status}</span>{" "}
                      {a.message}
                    </li>
                  ))}
                </ul>
              </div>
            )}
            {logsForAgent.length > 0 && (
              <div className="orch-detail-block">
                <strong>Pipeline log (this agent)</strong>
                <ul className="orch-detail-list orch-detail-log">
                  {logsForAgent.slice(-12).map((l) => (
                    <li key={l.id}>
                      <span className="orch-muted">
                        [{l.stage}] {l.action}
                      </span>
                      : {l.detail}
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </>
        )}

        {node.kind === "kg_hub" && kg && (
          <div className="orch-detail-block">
            <strong>Contributions</strong>
            <p className="orch-detail-text">
              Structured graph from <code>knowledge_graph_builder</code>, fed by
              upstream agents (trends, insights, conflicts, aggregation). Edges
              in the 3D view show likely provenance into this hub.
            </p>
            <p className="orch-detail-meta">
              {kg.nodes?.length ?? 0} nodes · {kg.edges?.length ?? 0} edges
            </p>
          </div>
        )}

        {node.kind === "insight" && (
          <div className="orch-detail-block">
            <strong>Insight</strong>
            {insightDetail ? (
              <>
                <p className="orch-detail-text">{insightDetail.description}</p>
                {insightDetail.impact && (
                  <p className="orch-detail-meta">
                    Impact: {insightDetail.impact}
                  </p>
                )}
              </>
            ) : (
              <p className="orch-detail-text">
                {node.message?.trim() ||
                  "Insight details will fill in as generation completes."}
              </p>
            )}
          </div>
        )}

        {node.message && node.kind !== "agent" && (
          <div className="orch-graph-detail-row">
            <strong>Summary</strong>
            <span>{node.message}</span>
          </div>
        )}
      </div>
    </aside>
  );
}

export function OrchestrationModeling({
  run,
  logs,
  agentResults,
  storagePrefix,
  embedded = false,
  live = false,
}: Props) {
  const [selected, setSelected] = useState<OrchNode | null>(null);
  const [logHighlightIdx, setLogHighlightIdx] = useState<number | null>(null);

  const { nodes, edges } = useMemo(
    () =>
      buildOrchestrationModel(
        run.agent_activity,
        agentResults,
        run.track,
        run.source_file_ids?.length ?? 0,
        logs,
      ),
    [run.agent_activity, run.source_file_ids, run.track, agentResults, logs],
  );

  const dispatchOrderByAgent = useMemo(
    () => buildDispatchOrderMap(logs),
    [logs],
  );

  const agentNodeCount = nodes.filter((n) => n.kind === "agent").length;
  const dataCount = nodes.filter((n) => n.kind === "data").length;
  const hasKg = nodes.some((n) => n.kind === "kg_hub");
  const insightCount = nodes.filter((n) => n.kind === "insight").length;

  const highlightIds = useMemo(() => {
    const s = new Set<string>();
    if (
      logHighlightIdx != null &&
      logs[logHighlightIdx] &&
      logHighlightIdx >= 0
    ) {
      const id = logAgentToNodeId(logs[logHighlightIdx]!.agent);
      if (id) s.add(id);
    }
    return s;
  }, [logHighlightIdx, logs]);

  const summary = `Orchestration · ${agentNodeCount} agents · KG hub ${hasKg ? "on" : "off"} · ${insightCount} insights · ${dataCount} data groups`;

  const canvasRemountKey = useMemo(() => {
    if (!live) return undefined;
    const last = logs.length ? logs[logs.length - 1] : undefined;
    return `${run.slug}-n${nodes.length}-L${logs.length}-id${last?.id ?? 0}`;
  }, [live, run.slug, nodes.length, logs]);

  const scrubberId = live ? "orch-log-scrub-live" : "orch-log-scrub";

  const body = (
    <>
      <p className="orch-model-lede">
        Pyramid layout: orchestrator at the top, agents below,{" "}
        <strong>knowledge graph</strong> at the base with pink flow lines from{" "}
        <strong>insight generation</strong> through each insight into the graph.
        Click any node for activity, log excerpts, and pipeline role.
        {live && (
          <>
            {" "}
            Updates as agents finish—KG and insight satellites appear when their
            outputs land in the run.
          </>
        )}
      </p>
      <div className="orch-modeling-wrap">
        {logs.length > 0 && (
          <div className="orch-timeline-scrub">
            <label htmlFor={scrubberId}>
              Pipeline log focus (highlights agent node)
            </label>
            <input
              id={scrubberId}
              type="range"
              min={0}
              max={Math.max(0, logs.length - 1)}
              value={logHighlightIdx ?? logs.length - 1}
              onChange={(e) => setLogHighlightIdx(Number(e.target.value))}
            />
            <button
              type="button"
              className="nav-btn nav-btn-ghost orch-timeline-clear"
              onClick={() => setLogHighlightIdx(null)}
            >
              Clear highlight
            </button>
          </div>
        )}
        <div
          className={`orch-graph-layout ${selected ? "orch-graph-layout--drawer" : ""}`}
        >
          <OrchestrationGraph3D
            nodes={nodes}
            edges={edges}
            selectedId={selected?.id ?? null}
            highlightIds={highlightIds}
            onSelect={setSelected}
            dispatchOrderByAgent={dispatchOrderByAgent}
            autoRotate={!live}
            remountKey={canvasRemountKey}
            knowledgeGraph={
              agentResults.knowledge_graph_builder?.nodes?.length
                ? agentResults.knowledge_graph_builder
                : null
            }
          />
          {selected && (
            <NodeDetailPanel
              node={selected}
              run={run}
              logs={logs}
              agentResults={agentResults}
              onClose={() => setSelected(null)}
            />
          )}
        </div>
        <p className="orch-critical-path-hint">
          Critical path follows orchestrator dispatch order; magenta paths trace
          insight → knowledge graph synthesis.
        </p>
      </div>
    </>
  );

  if (embedded && live) {
    return (
      <div
        className="orch-live-showcase orch-live-showcase--full"
        aria-label="Live orchestration"
      >
        {body}
      </div>
    );
  }

  if (embedded) {
    return body;
  }

  return (
    <CollapsibleAnalysisSection
      title="Orchestration & knowledge graph"
      defaultOpen={false}
      summary={summary}
      storageKey={`${storagePrefix}:orch-model`}
    >
      {body}
    </CollapsibleAnalysisSection>
  );
}
