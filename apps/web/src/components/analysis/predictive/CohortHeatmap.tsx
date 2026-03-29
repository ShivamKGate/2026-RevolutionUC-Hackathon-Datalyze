import { HeatmapChart } from "../../charts";

type Props = {
  rows?: string[];
  cols?: string[];
  values?: number[][];
  title?: string;
};

export function CohortHeatmap({ rows, cols, values, title }: Props) {
  if (!rows || !cols || !values || values.length === 0) return null;

  return (
    <HeatmapChart
      rows={rows}
      cols={cols}
      values={values}
      title={title ?? "Cohort Analysis"}
    />
  );
}
