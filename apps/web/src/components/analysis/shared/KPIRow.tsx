import { KPICard } from "../../charts";
import type { KPICardProps } from "../../charts";

type Props = {
  items?: KPICardProps[];
};

export function KPIRow({ items }: Props) {
  if (!items || items.length === 0) return null;

  return (
    <div className="kpi-row">
      {items.map((kpi, i) => (
        <KPICard key={i} {...kpi} />
      ))}
    </div>
  );
}
