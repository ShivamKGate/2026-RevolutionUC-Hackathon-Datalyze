import type { PipelineRunLog } from "../lib/api";

export function formatStructuredLogLine(entry: PipelineRunLog): string {
  const d = entry.detail;
  const detailStr = typeof d === "string" ? d : JSON.stringify(d ?? "");
  return `[${entry.timestamp ?? "n/a"}] [${entry.stage}] [${entry.agent}] ${entry.action}: ${detailStr}`;
}

export function runningStepSummary(
  logs: PipelineRunLog[],
  pipelineLog: unknown,
): string {
  if (logs.length > 0) {
    return formatStructuredLogLine(logs[logs.length - 1]!);
  }
  const pl = Array.isArray(pipelineLog) ? pipelineLog : [];
  const lines = pl.filter(Boolean) as string[];
  if (lines.length > 0) return lines[lines.length - 1]!;
  return "Waiting for pipeline…";
}

const _COMPLETE_HINTS = [
  /finaliz/i,
  /complete/i,
  /\d+\s*\/\s*\d+/,
  /duration/i,
  /done\b/i,
  /success/i,
];

export function completedPipelineSummary(
  logs: PipelineRunLog[],
  pipelineLog: unknown,
): string {
  const pl = Array.isArray(pipelineLog) ? pipelineLog : [];
  const lines = logs.length > 0 ? logs.map(formatStructuredLogLine) : [...pl];
  const tail = lines.slice(-40);
  for (let i = tail.length - 1; i >= 0; i--) {
    const line = tail[i]!;
    for (const re of _COMPLETE_HINTS) {
      if (re.test(line)) {
        return line.length > 140 ? `${line.slice(0, 137)}…` : line;
      }
    }
  }
  const n = lines.length;
  return `Pipeline complete · ${n} log lines`;
}

export function agentActivitySummary(
  rows: { status: string; agent_name: string; message: string }[],
): string {
  if (!rows.length) return "No agent updates yet.";
  const last = rows[rows.length - 1]!;
  const busy = rows.filter((r) => /running|pending|active/i.test(r.status));
  if (busy.length) {
    const b = busy[busy.length - 1]!;
    return `${b.agent_name}: ${b.status} — ${(b.message || "").slice(0, 80)}`;
  }
  return `${last.agent_name}: ${last.status} — ${(last.message || "").slice(0, 80)}`;
}
