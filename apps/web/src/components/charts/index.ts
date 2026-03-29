/**
 * Reusable chart primitives (Phase 2.2).
 * Import from `components/charts` for analysis templates and track renderers.
 */

export { BarChart, type BarChartProps } from "./BarChart";
export { BubbleChart, type BubbleChartProps } from "./BubbleChart";
export { ChartFrame } from "./ChartFrame";
export { ConfidenceGauge, type ConfidenceGaugeProps } from "./ConfidenceGauge";
export { GanttChart, type GanttChartProps } from "./GanttChart";
export { HeatmapChart, type HeatmapChartProps } from "./HeatmapChart";
export { KPICard, type KPICardProps } from "./KPICard";
export { ParetoChart, type ParetoChartProps } from "./ParetoChart";
export { RadarChart, type RadarChartProps, type RadarDimension } from "./RadarChart";
export { RecommendationCard, type RecommendationCardProps } from "./RecommendationCard";
export { SankeyDiagram, type SankeyDiagramProps } from "./SankeyDiagram";
export { ScatterPlot, type ScatterPlotProps } from "./ScatterPlot";
export { TimeSeriesChart, type TimeSeriesChartProps } from "./TimeSeriesChart";
export { TornadoChart, type TornadoChartProps } from "./TornadoChart";
export { WaterfallChart, type WaterfallChartProps } from "./WaterfallChart";

export type {
  BubblePoint,
  GanttTask,
  SankeyLink,
  SankeyNode,
  ScatterPoint,
  TimeSeriesPoint,
  TornadoFactor,
  WaterfallStep,
} from "./types";

export { baseLayout, chartColors } from "./plotlyTheme";
