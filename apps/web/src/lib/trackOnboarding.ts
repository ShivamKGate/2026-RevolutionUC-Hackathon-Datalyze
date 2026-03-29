/**
 * Aligns Company settings (users.onboarding_path), upload track IDs, and
 * startPipelineRun / API file validation (analysis_track on uploaded_files).
 */

const TRACK_IDS = new Set([
  "predictive",
  "automation",
  "optimization",
  "supply_chain",
]);

/**
 * Map API user.onboarding_path → track id used by listUploadedFiles(?track=).
 */
export function onboardingPathToAnalysisTrackId(
  path: string | null | undefined,
): string {
  if (!path) return "predictive";
  const p = path.trim();
  const lower = p.toLowerCase();

  if (lower === "deep_analysis") return "predictive";
  if (lower === "automations") return "automation";
  if (lower === "business_automations") return "optimization";
  if (lower === "supply_chain") return "supply_chain";

  if (p === "Deep Analysis") return "predictive";
  if (p === "DevOps/Automations") return "automation";
  if (p === "Business Automations") return "optimization";
  if (lower === "supply chain") return "supply_chain";

  if (TRACK_IDS.has(lower)) return lower;

  return "predictive";
}

/**
 * onboarding_path for POST /runs/start — must match backend ONBOARDING_PATH_TO_TRACK
 * (same strings as Upload page TRACKS[].onboarding).
 */
export function trackIdToStartOnboarding(trackId: string): string {
  const m: Record<string, string> = {
    predictive: "Deep Analysis",
    automation: "DevOps/Automations",
    optimization: "Business Automations",
    supply_chain: "supply_chain",
  };
  return m[trackId] ?? "Deep Analysis";
}

/** Normalize /me onboarding_path for Company settings <select> values. */
export function apiOnboardingPathToFormValue(
  path: string | null | undefined,
): string {
  const tid = onboardingPathToAnalysisTrackId(path);
  const rev: Record<string, string> = {
    predictive: "deep_analysis",
    automation: "automations",
    optimization: "business_automations",
    supply_chain: "supply_chain",
  };
  return rev[tid] ?? "deep_analysis";
}
