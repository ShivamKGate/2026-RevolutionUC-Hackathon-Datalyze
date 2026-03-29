import type { ChartPriorityEntry } from "./types";

export type SectionWithId = { id: string };

/** Higher score first; sections without a chart_id in the plan keep default order after scored ones. */
export function sortByChartPriority<T extends SectionWithId>(
  sections: T[],
  priority: ChartPriorityEntry[] | undefined,
): T[] {
  if (!priority?.length) return sections;
  const scoreMap = new Map(priority.map((p) => [p.chart_id, p.score]));
  const scored = sections.filter((s) => scoreMap.has(s.id));
  const unscored = sections.filter((s) => !scoreMap.has(s.id));
  scored.sort((a, b) => scoreMap.get(b.id)! - scoreMap.get(a.id)!);
  return [...scored, ...unscored];
}
