import "./charts.css";

export type KPICardProps = {
  title: string;
  value: string | number;
  previousValue?: string | number;
  changePct?: number;
  trend?: "up" | "down" | "flat";
  confidence?: number;
  className?: string;
};

function formatValue(v: string | number): string {
  if (typeof v === "number" && Number.isFinite(v)) {
    if (Math.abs(v) >= 1_000_000) return `${(v / 1_000_000).toFixed(2)}M`;
    if (Math.abs(v) >= 1_000) return `${(v / 1_000).toFixed(1)}k`;
    return v.toLocaleString(undefined, { maximumFractionDigits: 2 });
  }
  return String(v);
}

export function KPICard({
  title,
  value,
  previousValue,
  changePct,
  trend,
  confidence,
  className = "",
}: KPICardProps) {
  const trendClass =
    trend === "up"
      ? "kpi-card-trend--up"
      : trend === "down"
        ? "kpi-card-trend--down"
        : "";

  return (
    <div className={`kpi-card ${className}`.trim()}>
      <p className="kpi-card-title">{title}</p>
      <p className="kpi-card-value">{formatValue(value)}</p>
      <div className="kpi-card-meta">
        {previousValue != null && (
          <span>Prev: {formatValue(previousValue)}</span>
        )}
        {changePct != null && (
          <span className={trendClass}>
            {changePct >= 0 ? "+" : ""}
            {changePct.toFixed(1)}%
          </span>
        )}
        {confidence != null && Number.isFinite(confidence) && (
          <span className="kpi-card-confidence">
            {(confidence * 100).toFixed(0)}% conf.
          </span>
        )}
      </div>
    </div>
  );
}
