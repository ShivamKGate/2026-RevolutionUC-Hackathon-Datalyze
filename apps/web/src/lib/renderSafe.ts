/**
 * Coerce API payloads that sometimes return structured objects where the UI
 * expects strings or numbers (e.g. confidence blocks with { basis, overall_confidence }).
 */

export function unknownToDisplayText(value: unknown, maxLen = 8000): string {
  if (value == null) return "";
  if (typeof value === "string") return value.slice(0, maxLen);
  if (typeof value === "number" || typeof value === "boolean") {
    return String(value);
  }
  if (typeof value === "object") {
    const o = value as Record<string, unknown>;
    if (
      "basis" in o ||
      "overall_confidence" in o ||
      "summary" in o ||
      "text" in o
    ) {
      const basis =
        typeof o.basis === "string"
          ? o.basis
          : typeof o.summary === "string"
            ? o.summary
            : typeof o.text === "string"
              ? o.text
              : "";
      const oc = o.overall_confidence;
      let pct = "";
      if (typeof oc === "number" && Number.isFinite(oc)) {
        const p = oc <= 1 ? Math.round(oc * 100) : Math.round(oc);
        pct = ` (${p}% confidence)`;
      }
      const line = `${basis}${pct}`.trim();
      if (line) return line.slice(0, maxLen);
    }
    try {
      return JSON.stringify(value).slice(0, maxLen);
    } catch {
      return "[unserializable]";
    }
  }
  return String(value).slice(0, maxLen);
}

/** Numeric score for ConfidenceStrip: number or { overall_confidence: number } */
export function coerceConfidenceScore(raw: unknown): number | null {
  if (raw == null) return null;
  if (typeof raw === "number" && Number.isFinite(raw)) return raw;
  if (typeof raw === "string") {
    const n = parseFloat(raw);
    return Number.isFinite(n) ? n : null;
  }
  if (typeof raw === "object" && raw !== null) {
    const o = raw as Record<string, unknown>;
    const inner = o.overall_confidence;
    if (typeof inner === "number" && Number.isFinite(inner)) return inner;
    if (typeof inner === "string") {
      const n = parseFloat(inner);
      return Number.isFinite(n) ? n : null;
    }
  }
  return null;
}
