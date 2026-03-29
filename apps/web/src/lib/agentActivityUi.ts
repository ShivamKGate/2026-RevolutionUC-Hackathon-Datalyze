/** CSS modifier classes for agent activity row status (semantic color). */
export function agentActivityStatusClass(status: string): string {
  const s = (status || "").toLowerCase();
  const base = "agent-activity-status";
  if (s === "failed" || s === "error") {
    return `${base} agent-activity-status--failed`;
  }
  if (s === "skipped") {
    return `${base} agent-activity-status--muted`;
  }
  if (s === "running" || s === "started" || s === "pending") {
    return `${base} agent-activity-status--running`;
  }
  return `${base} agent-activity-status--ok`;
}
