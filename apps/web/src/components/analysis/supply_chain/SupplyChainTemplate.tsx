import { useMemo } from "react";
import {
  BarChart,
  HeatmapChart,
  ParetoChart,
  ScatterPlot,
  TimeSeriesChart,
  type ScatterPoint,
} from "../../charts";
import type { AgentResults } from "../types";
import { KPIRow } from "../shared/KPIRow";
import { RecommendationsPanel } from "../shared/RecommendationsPanel";
import { ConfidencePanel } from "../shared/ConfidencePanel";
import { ExecutiveSummarySection } from "../shared/ExecutiveSummarySection";
import type { RecommendationCardProps } from "../../charts";
import "../analysis.css";

function NetworkFlowMap() {
  const nodes = [
    { id: "s1", label: "Suppliers", x: 10, y: 30, health: "ok" },
    { id: "w1", label: "Regional DC", x: 40, y: 20, health: "warn" },
    { id: "w2", label: "Hub WH", x: 40, y: 50, health: "ok" },
    { id: "d1", label: "Distribution", x: 70, y: 35, health: "ok" },
    { id: "c1", label: "Customers", x: 92, y: 35, health: "ok" },
  ];
  return (
    <section className="analysis-section">
      <h3 className="analysis-section-title">Network flow</h3>
      <div className="sc-network">
        <svg viewBox="0 0 100 60" className="sc-network-svg">
          <defs>
            <marker
              id="arrow"
              markerWidth="6"
              markerHeight="6"
              refX="5"
              refY="3"
              orient="auto"
            >
              <path d="M0,0 L6,3 L0,6 Z" fill="#64748b" />
            </marker>
          </defs>
          {[0, 1, 2, 3].map((i) => (
            <line
              key={i}
              x1={nodes[i]!.x + 6}
              y1={nodes[i]!.y + 4}
              x2={nodes[i + 1]!.x - 2}
              y2={nodes[i + 1]!.y + 4}
              stroke="#475569"
              strokeWidth="1.2"
              markerEnd="url(#arrow)"
            />
          ))}
          {nodes.map((n) => (
            <g key={n.id} transform={`translate(${n.x},${n.y})`}>
              <rect
                width="14"
                height="8"
                rx="1.5"
                fill={n.health === "warn" ? "#f59e0b" : "#22c55e"}
                opacity={0.85}
              />
              <text x="7" y="5" textAnchor="middle" fontSize="3" fill="#0f172a">
                {n.label.slice(0, 3)}
              </text>
            </g>
          ))}
        </svg>
        <p className="sc-network-caption">
          Edge thickness ∝ volume · Amber nodes need attention
        </p>
      </div>
    </section>
  );
}

function buildScatter(): ScatterPoint[] {
  return [
    { x: 96, y: 2, label: "Apex", color: "#22c55e" },
    { x: 91, y: 4, label: "Northwind", color: "#eab308" },
    { x: 88, y: 6, label: "BlueRiver", color: "#22c55e" },
    { x: 82, y: 9, label: "Harbor", color: "#ef4444" },
    { x: 79, y: 5, label: "Summit", color: "#eab308" },
  ];
}

function buildHeatmap(): {
  rows: string[];
  cols: string[];
  values: number[][];
} {
  const rows = ["Electronics", "Apparel", "Food", "Industrial"];
  const cols = ["M1", "M2", "M3", "M4", "M5", "M6"];
  const values = rows.map((_, ri) =>
    cols.map((_, ci) => 0.55 + 0.08 * Math.sin(ri + ci) + 0.02 * (ri - ci)),
  );
  return { rows, cols, values };
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

export function SupplyChainTemplate({
  agentResults,
}: {
  agentResults: AgentResults;
}) {
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

  const tf = agentResults.trend_forecasting;
  const series = useMemo(() => {
    const fc = tf?.forecasts?.[0];
    if (fc?.historical?.length) {
      return fc.historical.slice(-18).map((p) => ({
        date: p.date,
        value: p.value,
      }));
    }
    const y = new Date().getFullYear();
    return Array.from({ length: 12 }, (_, i) => ({
      date: `${y}-${String(i + 1).padStart(2, "0")}`,
      value: 1200 + i * 35 + (i % 3) * 20,
    }));
  }, [tf]);

  const heat = useMemo(() => buildHeatmap(), []);

  return (
    <div className="analysis-track-inner">
      <KPIRow items={kpis} />
      <div className="analysis-two-col">
        <section className="analysis-section">
          <h3 className="analysis-section-title">Lead time distribution</h3>
          <TimeSeriesChart series={series} title="" />
        </section>
        <section className="analysis-section">
          <h3 className="analysis-section-title">
            Inventory health by category
          </h3>
          <BarChart
            categories={["Healthy", "Overstock", "Stockout risk", "Dead stock"]}
            values={[54, 18, 12, 6]}
            title=""
          />
        </section>
      </div>
      <NetworkFlowMap />
      <div className="analysis-two-col">
        <section className="analysis-section">
          <h3 className="analysis-section-title">Supplier reliability</h3>
          <ScatterPlot
            points={buildScatter()}
            xLabel="On-time %"
            yLabel="Defect rate %"
            title=""
          />
        </section>
        <section className="analysis-section">
          <h3 className="analysis-section-title">Demand vs fulfillment</h3>
          <HeatmapChart
            rows={heat.rows}
            cols={heat.cols}
            values={heat.values}
            title=""
            colorScale="RdYlGn"
          />
        </section>
      </div>
      <section className="analysis-section">
        <h3 className="analysis-section-title">Order delay root causes</h3>
        <ParetoChart
          categories={[
            "Carrier",
            "Customs",
            "Forecast error",
            "Supplier late",
            "Other",
          ]}
          values={[42, 28, 14, 10, 6]}
          title=""
        />
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
