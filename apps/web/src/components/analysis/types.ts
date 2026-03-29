import type { TimeSeriesPoint } from "../charts";

/* ── trend_forecasting ───────────────────────────────────────────── */

export type ForecastMetric = {
  metric: string;
  historical: TimeSeriesPoint[];
  predicted: TimeSeriesPoint[];
  confidence: number;
  trend_direction: string;
  seasonality_detected: boolean;
};

export type Driver = {
  factor: string;
  impact_pct: number;
};

export type Anomaly = {
  date: string;
  metric: string;
  expected: number;
  actual: number;
  root_cause: string;
};

export type TrendForecastingOutput = {
  forecasts: ForecastMetric[];
  drivers: Driver[];
  anomalies: Anomaly[];
};

/* ── insight_generation ──────────────────────────────────────────── */

export type InsightData = {
  current: number;
  previous: number;
  change_pct: number;
};

export type Insight = {
  title: string;
  description: string;
  impact: string;
  confidence: number;
  chart_type: string;
  data: InsightData;
};

export type InsightRecommendation = {
  action: string;
  priority: "high" | "medium" | "low";
  expected_impact: string;
  confidence: number;
};

export type InsightGenerationOutput = {
  insights: Insight[];
  recommendations: InsightRecommendation[];
};

/* ── automation_strategy ─────────────────────────────────────────── */

export type AutomationProcess = {
  name: string;
  current_time_hours: number;
  automated_time_hours: number;
  cost_current: number;
  cost_automated: number;
  roi_months: number;
  implementation_effort: string;
  impact_score: number;
};

export type Bottleneck = {
  stage: string;
  time_pct: number;
  cost_pct: number;
};

export type SOPDraft = {
  steps: string[];
  estimated_savings_annual: number;
};

export type AutomationStrategyOutput = {
  processes: AutomationProcess[];
  bottlenecks: Bottleneck[];
  sop_draft: SOPDraft;
};

/* ── executive_summary ───────────────────────────────────────────── */

export type ExecutiveSummaryOutput = {
  headline: string;
  situation_overview: string;
  key_findings: string[];
  risk_highlights: string[];
  next_actions: string[];
  confidence_statement: string;
};

/* ── output_evaluator (VisualizationPlan) ────────────────────────── */

export type EvaluatorKPI = {
  metric: string;
  value: string | number;
  change: string;
  source_agent: string;
};

export type EvaluatorChart = {
  type: string;
  title: string;
  data_source_agent: string;
  priority: number;
  chart_id?: string;
  metric?: string;
};

export type ChartPriorityEntry = {
  chart_id: string;
  score: number;
  reason?: string;
};

export type EvaluatorRecommendation = {
  text: string;
  confidence: number;
  source_agent: string;
};

export type ConfidenceBreakdown = {
  data_quality: number;
  analysis_depth: number;
  actionability: number;
};

export type VisualizationPlan = {
  kpi_cards: EvaluatorKPI[];
  charts: EvaluatorChart[];
  recommendations: EvaluatorRecommendation[];
  knowledge_graph: { available: boolean; node_count: number };
  overall_confidence: number;
  confidence_breakdown: ConfidenceBreakdown;
  chart_priority?: ChartPriorityEntry[];
};

/* ── knowledge_graph_builder ─────────────────────────────────────── */

export type KGNode = {
  id: string;
  label: string;
  type: string;
  value: number;
  context: string;
  insights: string[];
};

export type KGEdge = {
  source: string;
  target: string;
  relationship: string;
  strength: number;
};

export type KGCluster = {
  name: string;
  node_ids: string[];
};

export type KnowledgeGraphOutput = {
  nodes: KGNode[];
  edges: KGEdge[];
  clusters: KGCluster[];
};

/* ── Aggregate ───────────────────────────────────────────────────── */

export type AgentResults = {
  trend_forecasting?: TrendForecastingOutput;
  insight_generation?: InsightGenerationOutput;
  automation_strategy?: AutomationStrategyOutput;
  executive_summary?: ExecutiveSummaryOutput;
  output_evaluator?: VisualizationPlan;
  knowledge_graph_builder?: KnowledgeGraphOutput;
  conflict_detection?: {
    contradictions?: Array<Record<string, unknown>>;
  };
  swot_analysis?: Record<string, unknown>;
  sentiment_analysis?: Record<string, unknown>;
};
