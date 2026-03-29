import type { ReactNode } from "react";
import "./charts.css";

type ChartFrameProps = {
  title: string;
  children: ReactNode;
  className?: string;
};

export function ChartFrame({ title, children, className = "" }: ChartFrameProps) {
  return (
    <div className={`chart-frame ${className}`.trim()}>
      <h3 className="chart-frame-title">{title}</h3>
      <div className="chart-frame-body">{children}</div>
    </div>
  );
}
