import { useMemo, type ReactNode } from "react";
import { RadarChart } from "../../charts";
import type {
  KPICardProps,
  RadarDimension,
  RecommendationCardProps,
} from "../../charts";
import type { AgentResults, VisualizationPlan } from "../types";
import { sortByChartPriority } from "../chartSectionOrder";
import { KPIRow } from "../shared/KPIRow";
import { RecommendationsPanel } from "../shared/RecommendationsPanel";
import { ConfidenceStrip } from "../shared/ConfidenceStrip";
import { ExecutiveSummarySection } from "../shared/ExecutiveSummarySection";
import { CollapsibleAnalysisSection } from "../shared/CollapsibleAnalysisSection";
import { ForecastPanel } from "./ForecastPanel";
import { DriverWaterfall } from "./DriverWaterfall";
import { CohortHeatmap } from "./CohortHeatmap";
import { AnomalyTimeline } from "./AnomalyTimeline";
import { SegmentForecasts } from "./SegmentForecasts";
import "../analysis.css";

type Props = {
  agentResults: AgentResults;
  visualizationPlan?: VisualizationPlan;
  collapseStoragePrefix?: string;
  cohortData?: { rows: string[]; cols: string[]; values: number[][] };
  segmentForecasts?: AgentResults["trend_forecasting"];
  hideConfidenceStrip?: boolean;
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
  if (!Array.isArray(insights) || !insights.length) return null;
  return insights.slice(0, 8).map((ins) => ({
    label: ins.title,
    current: ins.data?.current ?? 0,
    predicted: ins.data?.current
      ? ins.data.current * (1 + (ins.data.change_pct ?? 0) / 100)
      : 0,
  }));
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

export function PredictiveTemplate({
  agentResults,
  visualizationPlan,
  collapseStoragePrefix = "",
  cohortData,
  segmentForecasts,
  hideConfidenceStrip = false,
}: Props) {
  const forecasting = agentResults.trend_forecasting;
  const evaluator = agentResults.output_evaluator;
  const radar = buildRadar(agentResults);
  const p = collapseStoragePrefix;

  const chartBlocks = useMemo(() => {
    const blocks: { id: string; summary: ReactNode; node: ReactNode }[] = [];
    if (forecasting?.forecasts?.length) {
      const m = forecasting.forecasts[0]?.metric ?? "KPIs";
      blocks.push({
        id: "forecast_panel",
        summary: `${forecasting.forecasts.length} metric(s) · primary: ${m}`,
        node: <ForecastPanel forecasts={forecasting.forecasts} />,
      });
    }
    if (forecasting?.drivers?.length) {
      const d0 = forecasting.drivers[0];
      blocks.push({
        id: "driver_waterfall",
        summary: d0
          ? `Largest driver: ${d0.factor} (${d0.impact_pct?.toFixed?.(0) ?? "?"}%)`
          : "Sensitivity drivers",
        node: <DriverWaterfall drivers={forecasting.drivers} />,
      });
    }
    if (radar) {
      blocks.push({
        id: "insight_radar",
        summary: `${radar.length} insight dimensions — current vs predicted`,
        node: (
          <section className="analysis-section">
            <h3 className="analysis-section-title">Current vs Predicted</h3>
            <RadarChart dimensions={radar} title="Insight Dimensions" />
          </section>
        ),
      });
    }
    blocks.push({
      id: "cohort_heatmap",
      summary: cohortData?.rows?.length
        ? `${cohortData.rows.length}×${cohortData.cols?.length ?? 0} cohort grid`
        : "Cohort / demand heatmap",
      node: (
        <CohortHeatmap
          rows={cohortData?.rows}
          cols={cohortData?.cols}
          values={cohortData?.values}
        />
      ),
    });
    if (forecasting?.anomalies?.length) {
      blocks.push({
        id: "anomaly_timeline",
        summary: `${forecasting.anomalies.length} anomaly event(s)`,
        node: <AnomalyTimeline anomalies={forecasting.anomalies} />,
      });
    }
    if ((forecasting?.forecasts?.length ?? 0) > 1) {
      blocks.push({
        id: "segment_forecasts",
        summary: "Per-segment forecast panels",
        node: (
          <SegmentForecasts
            segments={(segmentForecasts ?? forecasting)?.forecasts}
          />
        ),
      });
    }
    return sortByChartPriority(blocks, visualizationPlan?.chart_priority);
  }, [
    cohortData,
    forecasting?.anomalies,
    forecasting?.drivers,
    forecasting?.forecasts,
    radar,
    segmentForecasts?.forecasts,
    visualizationPlan?.chart_priority,
  ]);

  const titles: Record<string, string> = {
    forecast_panel: "Forecasts",
    driver_waterfall: "Driver waterfall",
    insight_radar: "Insight radar",
    cohort_heatmap: "Cohort heatmap",
    anomaly_timeline: "Anomaly timeline",
    segment_forecasts: "Segment forecasts",
  };

  return (
    <div className="analysis-track-inner">
      <KPIRow items={buildKPIs(agentResults)} />

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

      {chartBlocks.map((b) => (
        <CollapsibleAnalysisSection
          key={b.id}
          title={titles[b.id] ?? b.id}
          defaultOpen={false}
          summary={b.summary}
          storageKey={p ? `${p}:chart:${b.id}` : undefined}
        >
          {b.node}
        </CollapsibleAnalysisSection>
      ))}

      <ExecutiveSummarySection data={agentResults.executive_summary} />
    </div>
  );
}
