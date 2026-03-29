/** Shared prop types for chart primitives (Phase 2.2). */

export type TimeSeriesPoint = {
  date: string;
  value: number;
  lower?: number;
  upper?: number;
};

export type WaterfallStepType = "increase" | "decrease" | "total";

export type WaterfallStep = {
  label: string;
  value: number;
  type: WaterfallStepType;
};

export type SankeyNode = { id: string; label: string };
export type SankeyLink = {
  source: string;
  target: string;
  value: number;
};

export type BubblePoint = {
  x: number;
  y: number;
  size: number;
  label: string;
  color?: string;
};

export type ScatterPoint = {
  x: number;
  y: number;
  label?: string;
  color?: string;
};

export type TornadoFactor = {
  label: string;
  low: number;
  high: number;
  baseline: number;
};

export type GanttTask = {
  name: string;
  start: string;
  end: string;
  dependencies?: string[];
};
