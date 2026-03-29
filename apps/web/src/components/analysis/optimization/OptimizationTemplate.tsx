import { useMemo, useState } from "react";
import {
  BarChart,
  GanttChart,
  TornadoChart,
  type GanttTask,
  type TornadoFactor,
} from "../../charts";
import type { AgentResults } from "../types";
import { KPIRow } from "../shared/KPIRow";
import { RecommendationsPanel } from "../shared/RecommendationsPanel";
import { ConfidencePanel } from "../shared/ConfidencePanel";
import { ExecutiveSummarySection } from "../shared/ExecutiveSummarySection";
import type { RecommendationCardProps } from "../../charts";
import "../analysis.css";

type TreeNode = {
  label: string;
  value: string;
  delta?: string;
  children?: TreeNode[];
};

function ProfitTreeSection({ root }: { root: TreeNode }) {
  const [open, setOpen] = useState<Record<string, boolean>>({ root: true });
  const toggle = (k: string) => setOpen((o) => ({ ...o, [k]: !o[k] }));

  function NodeView(n: TreeNode, path: string, depth: number) {
    const key = path + n.label;
    const hasKids = (n.children?.length ?? 0) > 0;
    const expanded = open[key] ?? depth < 2;
    return (
      <div
        key={key}
        className="opt-tree-node"
        style={{ marginLeft: depth * 16 }}
      >
        <div className="opt-tree-row">
          {hasKids ? (
            <button
              type="button"
              className="opt-tree-toggle"
              onClick={() => toggle(key)}
            >
              {expanded ? "−" : "+"}
            </button>
          ) : (
            <span className="opt-tree-toggle-spacer" />
          )}
          <span className="opt-tree-label">{n.label}</span>
          <span className="opt-tree-value">{n.value}</span>
          {n.delta && (
            <span
              className={
                "opt-tree-delta " +
                (n.delta.startsWith("-")
                  ? "neg"
                  : n.delta === "flat"
                    ? ""
                    : "pos")
              }
            >
              {n.delta}
            </span>
          )}
        </div>
        {hasKids &&
          expanded &&
          n.children!.map((c) => NodeView(c, key + "/", depth + 1))}
      </div>
    );
  }

  return (
    <section className="analysis-section">
      <h3 className="analysis-section-title">Profit &amp; cost tree</h3>
      <div className="opt-profit-tree">{NodeView(root, "", 0)}</div>
    </section>
  );
}

function buildProfitTree(results: AgentResults): TreeNode {
  const ig = results.insight_generation;
  const first = ig?.insights?.[0];
  return {
    label: "Net performance",
    value: first?.data?.current != null ? String(first.data.current) : "—",
    delta:
      first?.data?.change_pct != null
        ? `${first.data.change_pct > 0 ? "+" : ""}${first.data.change_pct.toFixed(1)}%`
        : undefined,
    children: [
      {
        label: "Revenue streams",
        value: "Multi-channel",
        children: [
          { label: "Product revenue", value: "62%", delta: "+4.2%" },
          { label: "Service revenue", value: "38%", delta: "flat" },
        ],
      },
      {
        label: "Operating leverage",
        value: "Costs",
        children: [
          { label: "Labor & ops", value: "41%", delta: "-1.1%" },
          { label: "Technology", value: "12%", delta: "+0.8%" },
        ],
      },
    ],
  };
}

function buildConstraintBars(results: AgentResults): {
  categories: string[];
  values: number[];
} {
  const rows = results.conflict_detection?.contradictions as
    | { description?: string }[]
    | undefined;
  if (rows?.length) {
    return {
      categories: rows
        .slice(0, 5)
        .map((r, i) => r.description?.slice(0, 40) || `Constraint ${i + 1}`),
      values: rows.slice(0, 5).map((_, i) => 95 - i * 12),
    };
  }
  return {
    categories: [
      "Process friction",
      "Data latency",
      "Vendor variance",
      "Capacity",
      "Policy",
    ],
    values: [88, 72, 64, 55, 48],
  };
}

function buildTornado(results: AgentResults): TornadoFactor[] {
  const drivers = results.trend_forecasting?.drivers;
  if (drivers?.length) {
    return drivers.slice(0, 6).map((d) => ({
      label: d.factor,
      low: 0,
      high: Math.max(5, d.impact_pct),
      baseline: 100,
    }));
  }
  return [
    { label: "Price", low: 82, high: 118, baseline: 100 },
    { label: "Volume", low: 76, high: 112, baseline: 100 },
    { label: "Unit cost", low: 88, high: 124, baseline: 100 },
    { label: "FX", low: 91, high: 107, baseline: 100 },
  ];
}

function buildGantt(): GanttTask[] {
  const y = new Date().getFullYear();
  return [
    { name: "Q1 cost review", start: `${y}-01-01`, end: `${y}-03-15` },
    { name: "Vendor renegotiation", start: `${y}-02-01`, end: `${y}-05-30` },
    { name: "Automation pilot", start: `${y}-04-01`, end: `${y}-07-31` },
    { name: "Org design refresh", start: `${y}-06-01`, end: `${y}-09-30` },
  ];
}

function buildRecs(results: AgentResults): RecommendationCardProps[] {
  const ev = results.output_evaluator;
  if (ev?.recommendations?.length) {
    return ev.recommendations.map((r) => ({
      action: r.text,
      priority: "medium",
      impact: "",
      confidence: r.confidence,
      source_agent: r.source_agent,
    }));
  }
  const ig = results.insight_generation?.recommendations;
  if (ig?.length) {
    return ig.map((r) => ({
      action: r.action,
      priority: r.priority,
      impact: r.expected_impact,
      confidence: r.confidence,
      source_agent: "insight_generation",
    }));
  }
  return [];
}

export function OptimizationTemplate({
  agentResults,
}: {
  agentResults: AgentResults;
}) {
  const tree = useMemo(() => buildProfitTree(agentResults), [agentResults]);
  const constraints = useMemo(
    () => buildConstraintBars(agentResults),
    [agentResults],
  );
  const tornado = useMemo(() => buildTornado(agentResults), [agentResults]);
  const gantt = useMemo(() => buildGantt(), []);
  const evaluator = agentResults.output_evaluator;

  const kpis =
    evaluator?.kpi_cards?.map((k) => ({
      title: k.metric,
      value: k.value,
      changePct: parseFloat(String(k.change)) || undefined,
      trend:
        parseFloat(String(k.change)) > 0
          ? ("up" as const)
          : parseFloat(String(k.change)) < 0
            ? ("down" as const)
            : ("flat" as const),
    })) ?? [];

  return (
    <div className="analysis-track-inner">
      <KPIRow items={kpis} />
      <ProfitTreeSection root={tree} />
      <div className="analysis-two-col">
        <section className="analysis-section">
          <h3 className="analysis-section-title">Constraint impact (EBITDA)</h3>
          <BarChart
            categories={constraints.categories}
            values={constraints.values}
            title=""
            horizontal
          />
        </section>
        <section className="analysis-section">
          <h3 className="analysis-section-title">Sensitivity tornado</h3>
          <TornadoChart factors={tornado} title="" />
        </section>
      </div>
      <section className="analysis-section">
        <h3 className="analysis-section-title">Prioritized recommendations</h3>
        <table className="opt-rec-table">
          <thead>
            <tr>
              <th>Recommendation</th>
              <th>Priority</th>
              <th>Confidence</th>
            </tr>
          </thead>
          <tbody>
            {(buildRecs(agentResults).length
              ? buildRecs(agentResults)
              : [
                  {
                    action: "Run deeper data ingest for department-level costs",
                    priority: "high",
                    impact: "",
                    confidence: 0.62,
                    source_agent: "system",
                  },
                ]
            ).map((r, i) => (
              <tr key={i}>
                <td>{r.action}</td>
                <td>
                  <span className={`opt-pill opt-pill-${r.priority}`}>
                    {r.priority}
                  </span>
                </td>
                <td>{(r.confidence * 100).toFixed(0)}%</td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>
      <section className="analysis-section">
        <h3 className="analysis-section-title">Goal → action alignment</h3>
        <div className="opt-flow">
          <div className="opt-flow-col">
            <h4>Objectives</h4>
            <ul>
              <li>Margin expansion</li>
              <li>Operational resilience</li>
              <li>Customer retention</li>
            </ul>
          </div>
          <div className="opt-flow-arrow">→</div>
          <div className="opt-flow-col">
            <h4>Actions</h4>
            <ul>
              <li>Automate reconciliations</li>
              <li>Renegotiate vendor tiers</li>
              <li>Rightsize inventory</li>
            </ul>
          </div>
          <div className="opt-flow-arrow">→</div>
          <div className="opt-flow-col">
            <h4>Outcomes</h4>
            <ul>
              <li>Higher throughput</li>
              <li>Lower unit cost</li>
              <li>Stable NPS</li>
            </ul>
          </div>
        </div>
      </section>
      <section className="analysis-section">
        <h3 className="analysis-section-title">Optimization roadmap</h3>
        <GanttChart tasks={gantt} title="" />
      </section>
      <RecommendationsPanel recommendations={buildRecs(agentResults)} />
      <ConfidencePanel
        score={evaluator?.overall_confidence}
        breakdown={evaluator?.confidence_breakdown}
      />
      <ExecutiveSummarySection data={agentResults.executive_summary} />
    </div>
  );
}
