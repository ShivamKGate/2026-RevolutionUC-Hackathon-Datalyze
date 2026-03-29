import type { KPICardProps, RecommendationCardProps } from "../../charts";
import type { AgentResults } from "../types";
import { KPIRow } from "../shared/KPIRow";
import { RecommendationsPanel } from "../shared/RecommendationsPanel";
import { ConfidencePanel } from "../shared/ConfidencePanel";
import { ExecutiveSummarySection } from "../shared/ExecutiveSummarySection";
import { BottleneckSankey } from "./BottleneckSankey";
import { OpportunityMatrix } from "./OpportunityMatrix";
import { ROIBubbles } from "./ROIBubbles";
import { StrategicPriorities } from "./StrategicPriorities";
import { SOPPanel } from "./SOPPanel";
import { CapacityForecast } from "./CapacityForecast";
import "../analysis.css";

type Props = {
  agentResults: AgentResults;
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
  const avgRoi =
    procs.reduce((s, p) => s + p.roi_months, 0) / procs.length;

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

function buildRecommendations(results: AgentResults): RecommendationCardProps[] {
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

export function AutomationTemplate({ agentResults }: Props) {
  const automation = agentResults.automation_strategy;
  const evaluator = agentResults.output_evaluator;

  return (
    <div className="analysis-template">
      <KPIRow items={buildSummaryKPIs(agentResults)} />

      <BottleneckSankey bottlenecks={automation?.bottlenecks} />

      <OpportunityMatrix processes={automation?.processes} />

      <ROIBubbles processes={automation?.processes} />

      <StrategicPriorities processes={automation?.processes} />

      <SOPPanel sopDraft={automation?.sop_draft} />

      <CapacityForecast processes={automation?.processes} />

      <RecommendationsPanel
        recommendations={buildRecommendations(agentResults)}
      />

      <ConfidencePanel
        score={evaluator?.overall_confidence}
        breakdown={evaluator?.confidence_breakdown}
      />

      <ExecutiveSummarySection data={agentResults.executive_summary} />
    </div>
  );
}
