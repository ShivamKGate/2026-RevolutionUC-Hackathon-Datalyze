import { useMemo, type ReactNode } from "react";
import type { KPICardProps, RecommendationCardProps } from "../../charts";
import type { AgentResults, VisualizationPlan } from "../types";
import { sortByChartPriority } from "../chartSectionOrder";
import { KPIRow } from "../shared/KPIRow";
import { RecommendationsPanel } from "../shared/RecommendationsPanel";
import { ConfidenceStrip } from "../shared/ConfidenceStrip";
import { CollapsibleAnalysisSection } from "../shared/CollapsibleAnalysisSection";
import { BottleneckSankey } from "./BottleneckSankey";
import { OpportunityMatrix } from "./OpportunityMatrix";
import { ROIBubbles } from "./ROIBubbles";
import { StrategicPriorities } from "./StrategicPriorities";
import { SOPPanel } from "./SOPPanel";
import { CapacityForecast } from "./CapacityForecast";
import "../analysis.css";

type Props = {
  agentResults: AgentResults;
  visualizationPlan?: VisualizationPlan;
  collapseStoragePrefix?: string;
  hideConfidenceStrip?: boolean;
  runSlug: string;
  runStatus: string;
};

function formatCurrency(n: number): string {
  if (Math.abs(n) >= 1_000_000) return `$${(n / 1_000_000).toFixed(2)}M`;
  if (Math.abs(n) >= 1_000) return `$${(n / 1_000).toFixed(1)}k`;
  return `$${n.toFixed(0)}`;
}

function buildSummaryKPIs(results: AgentResults): KPICardProps[] {
  const procs = results.automation_strategy?.processes;
  if (!procs?.length) return [];

  const totalHoursSaved = procs.reduce(
    (s, p) => s + (p.current_time_hours - p.automated_time_hours),
    0,
  );
  const totalCostSaved = procs.reduce(
    (s, p) => s + (p.cost_current - p.cost_automated),
    0,
  );
  const avgRoi = procs.reduce((s, p) => s + p.roi_months, 0) / procs.length;

  return [
    {
      title: "Total Hours Saved",
      value: `${totalHoursSaved.toFixed(1)}h`,
      trend: "up" as const,
    },
    {
      title: "Total Cost Saved",
      value: formatCurrency(totalCostSaved),
      trend: "up" as const,
    },
    {
      title: "Avg ROI Period",
      value: `${avgRoi.toFixed(1)} mo`,
      trend: "down" as const,
    },
  ];
}

function buildRecommendations(
  results: AgentResults,
): RecommendationCardProps[] {
  const recs = results.output_evaluator?.recommendations;
  if (!recs?.length) return [];
  return recs.map((r) => ({
    action: r.text,
    priority: "medium" as const,
    impact: "",
    confidence: r.confidence,
    source_agent: r.source_agent,
  }));
}

function sankeySummary(b: AgentResults["automation_strategy"]): string {
  const top = b?.bottlenecks?.[0];
  if (!top) return "Process flow and bottlenecks";
  const hrs =
    top.time_pct != null ? `~${top.time_pct.toFixed(0)}% cycle time` : "";
  return `Top bottleneck: ${top.stage} — ${hrs}`.trim();
}

export function AutomationTemplate({
  agentResults,
  visualizationPlan,
  collapseStoragePrefix = "",
  hideConfidenceStrip = false,
  runSlug,
  runStatus,
}: Props) {
  const automation = agentResults.automation_strategy;
  const evaluator = agentResults.output_evaluator;
  const p = collapseStoragePrefix;

  const chartBlocks = useMemo(() => {
    const blocks: { id: string; summary: ReactNode; node: ReactNode }[] = [];
    if (automation?.bottlenecks?.length) {
      blocks.push({
        id: "bottleneck_sankey",
        summary: sankeySummary(automation),
        node: <BottleneckSankey bottlenecks={automation.bottlenecks} />,
      });
    }
    if (automation?.processes?.length) {
      blocks.push({
        id: "opportunity_matrix",
        summary: `${automation.processes.length} processes — impact vs effort`,
        node: <OpportunityMatrix processes={automation.processes} />,
      });
      blocks.push({
        id: "roi_bubbles",
        summary: "ROI and payback by process",
        node: <ROIBubbles processes={automation.processes} />,
      });
      blocks.push({
        id: "capacity_projection",
        summary: "Headcount / capacity outlook",
        node: <CapacityForecast processes={automation.processes} />,
      });
    }
    return sortByChartPriority(blocks, visualizationPlan?.chart_priority);
  }, [automation, visualizationPlan?.chart_priority]);

  return (
    <div className="analysis-track-inner">
      <KPIRow items={buildSummaryKPIs(agentResults)} />

      <div
        className={
          hideConfidenceStrip
            ? "analysis-top-row analysis-top-row--no-confidence"
            : "analysis-top-row"
        }
      >
        <RecommendationsPanel
          recommendations={buildRecommendations(agentResults)}
        />
        {!hideConfidenceStrip && (
          <ConfidenceStrip
            score={evaluator?.overall_confidence}
            breakdown={evaluator?.confidence_breakdown}
          />
        )}
      </div>

      {chartBlocks.length > 0 && (
        <section className="analysis-section automation-chart-section">
          <h3 className="analysis-section-title">Analysis charts</h3>
          <div className="automation-chart-section-stack">
            {chartBlocks.map((b) => (
              <CollapsibleAnalysisSection
                key={b.id}
                title={
                  b.id === "bottleneck_sankey"
                    ? "Process bottlenecks"
                    : b.id === "opportunity_matrix"
                      ? "Opportunity matrix"
                      : b.id === "roi_bubbles"
                        ? "ROI analysis"
                        : "Capacity projection"
                }
                defaultOpen={false}
                summary={b.summary}
                storageKey={p ? `${p}:chart:${b.id}` : undefined}
              >
                {b.node}
              </CollapsibleAnalysisSection>
            ))}
          </div>
        </section>
      )}

      <StrategicPriorities processes={automation?.processes} />

      <SOPPanel sopDraft={automation?.sop_draft} />
    </div>
  );
}
