import type { AgentResults, VisualizationPlan } from "./types";
import { PredictiveTemplate } from "./predictive/PredictiveTemplate";
import { AutomationTemplate } from "./automation/AutomationTemplate";
import { OptimizationTemplate } from "./optimization/OptimizationTemplate";
import { SupplyChainTemplate } from "./supply_chain/SupplyChainTemplate";
import "./analysis.css";

type Props = {
  track: string;
  agentResults: AgentResults;
  visualizationPlan?: VisualizationPlan;
  slug: string;
  runStatus: string;
  /** When true, hide the ConfidenceStrip (e.g. shown in analysis page header). */
  hideConfidenceStrip?: boolean;
};

export function TrackRenderer({
  track,
  agentResults,
  visualizationPlan,
  slug,
  runStatus,
  hideConfidenceStrip,
}: Props) {
  return (
    <div className="analysis-template">
      <TrackContent
        track={track}
        agentResults={agentResults}
        visualizationPlan={visualizationPlan}
        collapseStoragePrefix={slug}
        runSlug={slug}
        runStatus={runStatus}
        hideConfidenceStrip={hideConfidenceStrip}
      />
    </div>
  );
}

function TrackContent({
  track,
  agentResults,
  visualizationPlan,
  collapseStoragePrefix,
  runSlug,
  runStatus,
  hideConfidenceStrip,
}: {
  track: string;
  agentResults: AgentResults;
  visualizationPlan?: VisualizationPlan;
  collapseStoragePrefix: string;
  runSlug: string;
  runStatus: string;
  hideConfidenceStrip?: boolean;
}) {
  const common = {
    agentResults,
    visualizationPlan,
    collapseStoragePrefix,
    runSlug,
    runStatus,
    hideConfidenceStrip,
  };
  switch (track) {
    case "predictive":
      return <PredictiveTemplate {...common} />;
    case "automation":
      return <AutomationTemplate {...common} />;
    case "optimization":
      return <OptimizationTemplate {...common} />;
    case "supply_chain":
      return <SupplyChainTemplate {...common} />;
    default:
      return (
        <div className="analysis-coming-soon">
          <h3>{track ?? "Unknown"} Analysis</h3>
          <p>This analysis track is coming soon.</p>
        </div>
      );
  }
}
