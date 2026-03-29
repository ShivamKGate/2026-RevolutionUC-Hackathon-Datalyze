import { RadarChart } from "../../charts";
import type { KPICardProps, RadarDimension } from "../../charts";
import type { RecommendationCardProps } from "../../charts";
import type { AgentResults } from "../types";
import { KPIRow } from "../shared/KPIRow";
import { RecommendationsPanel } from "../shared/RecommendationsPanel";
import { ConfidencePanel } from "../shared/ConfidencePanel";
import { ExecutiveSummarySection } from "../shared/ExecutiveSummarySection";
import { ForecastPanel } from "./ForecastPanel";
import { DriverWaterfall } from "./DriverWaterfall";
import { CohortHeatmap } from "./CohortHeatmap";
import { AnomalyTimeline } from "./AnomalyTimeline";
import { SegmentForecasts } from "./SegmentForecasts";
import "../analysis.css";

type Props = {
  agentResults: AgentResults;
  cohortData?: { rows: string[]; cols: string[]; values: number[][] };
  segmentForecasts?: AgentResults["trend_forecasting"];
};

function buildKPIs(results: AgentResults): KPICardProps[] {
  const evaluator = results.output_evaluator;
  if (!evaluator?.kpi_cards?.length) return [];
  return evaluator.kpi_cards.map((k) => ({
    title: k.metric,
    value: k.value,
    changePct: parseFloat(String(k.change)) || undefined,
    trend:
      parseFloat(String(k.change)) > 0
        ? ("up" as const)
        : parseFloat(String(k.change)) < 0
          ? ("down" as const)
          : ("flat" as const),
  }));
}

function buildRadar(results: AgentResults): RadarDimension[] | null {
  const insights = results.insight_generation?.insights;
  if (!insights?.length) return null;
  return insights.slice(0, 8).map((ins) => ({
    label: ins.title,
    current: ins.data?.current ?? 0,
    predicted: ins.data?.current
      ? ins.data.current * (1 + (ins.data.change_pct ?? 0) / 100)
      : 0,
  }));
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

export function PredictiveTemplate({
  agentResults,
  cohortData,
  segmentForecasts,
}: Props) {
  const forecasting = agentResults.trend_forecasting;
  const evaluator = agentResults.output_evaluator;
  const radar = buildRadar(agentResults);

  return (
    <div className="analysis-template">
      <KPIRow items={buildKPIs(agentResults)} />

      <ForecastPanel forecasts={forecasting?.forecasts} />

      <DriverWaterfall drivers={forecasting?.drivers} />

      {radar && (
        <section className="analysis-section">
          <h3 className="analysis-section-title">Current vs Predicted</h3>
          <RadarChart dimensions={radar} title="Insight Dimensions" />
        </section>
      )}

      <CohortHeatmap
        rows={cohortData?.rows}
        cols={cohortData?.cols}
        values={cohortData?.values}
      />

      <AnomalyTimeline anomalies={forecasting?.anomalies} />

      <SegmentForecasts segments={segmentForecasts?.forecasts} />

      <RecommendationsPanel recommendations={buildRecommendations(agentResults)} />

      <ConfidencePanel
        score={evaluator?.overall_confidence}
        breakdown={evaluator?.confidence_breakdown}
      />

      <ExecutiveSummarySection data={agentResults.executive_summary} />
    </div>
  );
}
