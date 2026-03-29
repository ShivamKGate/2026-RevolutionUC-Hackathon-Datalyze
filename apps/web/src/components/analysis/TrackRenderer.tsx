import type { AgentResults, VisualizationPlan } from "./types";
import { ExportButton } from "./shared/ExportButton";
import { PredictiveTemplate } from "./predictive/PredictiveTemplate";
import { AutomationTemplate } from "./automation/AutomationTemplate";
import "./analysis.css";

type Props = {
  track: string;
  agentResults: AgentResults;
  visualizationPlan?: VisualizationPlan;
  slug: string;
};

export function TrackRenderer({ track, agentResults, slug }: Props) {
  return (
    <div className="analysis-template">
      <div className="analysis-header">
        <ExportButton slug={slug} />
      </div>
      <TrackContent track={track} agentResults={agentResults} />
    </div>
  );
}

function TrackContent({
  track,
  agentResults,
}: {
  track: string;
  agentResults: AgentResults;
}) {
  switch (track) {
    case "predictive":
      return <PredictiveTemplate agentResults={agentResults} />;
    case "automation":
      return <AutomationTemplate agentResults={agentResults} />;
    default:
      return (
        <div className="analysis-coming-soon">
          <h3>{track ?? "Unknown"} Analysis</h3>
          <p>This analysis track is coming soon.</p>
        </div>
      );
  }
}
