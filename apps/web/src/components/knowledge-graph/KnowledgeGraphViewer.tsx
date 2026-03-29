import { useState, useMemo, useCallback, useRef, useEffect } from "react";
import ForceGraph2D from "react-force-graph-2d";
import "./knowledge-graph.css";

const CLUSTER_PALETTE = [
  "#2563eb", "#8b5cf6", "#06b6d4", "#f59e0b", "#10b981",
  "#ef4444", "#ec4899", "#f97316", "#14b8a6", "#6366f1",
  "#84cc16", "#e879f9", "#22d3ee", "#fb923c", "#a78bfa",
];

export type KGNode = {
  id: string;
  label: string;
  type: string;
  value: number;
  context: string;
  insights: string[];
};

export type KGEdge = {
  source: string;
  target: string;
  relationship: string;
  strength: number;
};

export type KGCluster = {
  name: string;
  node_ids: string[];
};

export type KnowledgeGraphViewerProps = {
  nodes: KGNode[];
  edges: KGEdge[];
  clusters: KGCluster[];
  title?: string;
  collapsed?: boolean;
};

type InternalNode = KGNode & { color: string; clusterName: string };

export function KnowledgeGraphViewer({
  nodes,
  edges,
  clusters,
  title = "Knowledge Graph",
  collapsed: initialCollapsed = false,
}: KnowledgeGraphViewerProps) {
  const [expanded, setExpanded] = useState(!initialCollapsed);
  const [selectedNode, setSelectedNode] = useState<InternalNode | null>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const [dimensions, setDimensions] = useState({ width: 800, height: 500 });

  useEffect(() => {
    if (!containerRef.current || !expanded) return;
    const observer = new ResizeObserver((entries) => {
      const entry = entries[0];
      if (entry) {
        setDimensions({
          width: entry.contentRect.width,
          height: Math.max(400, entry.contentRect.height),
        });
      }
    });
    observer.observe(containerRef.current);
    return () => observer.disconnect();
  }, [expanded]);

  const clusterColorMap = useMemo(() => {
    const map = new Map<string, string>();
    clusters.forEach((c, i) => {
      map.set(c.name, CLUSTER_PALETTE[i % CLUSTER_PALETTE.length]);
    });
    return map;
  }, [clusters]);

  const nodeClusterMap = useMemo(() => {
    const map = new Map<string, { color: string; clusterName: string }>();
    clusters.forEach((c) => {
      const color = clusterColorMap.get(c.name) ?? CLUSTER_PALETTE[0];
      c.node_ids.forEach((id) => map.set(id, { color, clusterName: c.name }));
    });
    return map;
  }, [clusters, clusterColorMap]);

  const graphData = useMemo(() => {
    const internalNodes: InternalNode[] = nodes.map((n) => {
      const info = nodeClusterMap.get(n.id);
      return {
        ...n,
        color: info?.color ?? "#64748b",
        clusterName: info?.clusterName ?? "Unclustered",
      };
    });
    const links = edges.map((e) => ({
      source: e.source,
      target: e.target,
      relationship: e.relationship,
      strength: e.strength,
    }));
    return { nodes: internalNodes, links };
  }, [nodes, edges, nodeClusterMap]);

  const maxStrength = useMemo(
    () => Math.max(1, ...edges.map((e) => e.strength)),
    [edges],
  );

  const handleNodeClick = useCallback((node: any) => {
    setSelectedNode(node as InternalNode);
  }, []);

  const isEmpty = nodes.length === 0;

  if (initialCollapsed) {
    return (
      <div>
        <button
          className="kg-collapsed-toggle"
          aria-expanded={expanded}
          onClick={() => setExpanded((v) => !v)}
        >
          <span>{title}</span>
          <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
            <path d="M4 6l4 4 4-4" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
          </svg>
        </button>
        {expanded && (
          <div className="kg-wrapper" style={{ marginTop: "0.5rem" }}>
            {renderContent()}
          </div>
        )}
      </div>
    );
  }

  return <div className="kg-wrapper">{renderContent()}</div>;

  function renderContent() {
    return (
      <>
        <div className="kg-header">
          <h3 className="kg-title">{title}</h3>
          {clusters.length > 0 && (
            <div className="kg-legend">
              {clusters.map((c) => (
                <span key={c.name} className="kg-legend-item">
                  <span
                    className="kg-legend-dot"
                    style={{ background: clusterColorMap.get(c.name) }}
                  />
                  {c.name}
                </span>
              ))}
            </div>
          )}
        </div>

        <div className="kg-body" ref={containerRef}>
          {isEmpty ? (
            <div className="kg-empty">
              No knowledge graph data available yet. Run an analysis to generate the graph.
            </div>
          ) : (
            <ForceGraph2D
              graphData={graphData}
              width={dimensions.width}
              height={dimensions.height}
              backgroundColor="#0f172a"
              nodeLabel={(node: any) => node.label}
              nodeColor={(node: any) => node.color}
              nodeVal={(node: any) => Math.max(2, node.value)}
              linkLabel={(link: any) => link.relationship}
              linkWidth={(link: any) =>
                1 + (link.strength / maxStrength) * 4
              }
              linkColor={() => "rgba(148,163,184,0.35)"}
              linkDirectionalParticles={1}
              onNodeClick={handleNodeClick}
              nodeCanvasObject={(node: any, ctx: CanvasRenderingContext2D, globalScale: number) => {
                const label = node.label as string;
                const size = Math.max(3, Math.sqrt(node.value ?? 4) * 2);
                const fontSize = Math.min(12 / globalScale, 4);
                const color = node.color as string;

                ctx.beginPath();
                ctx.arc(node.x, node.y, size, 0, 2 * Math.PI);
                ctx.fillStyle = color;
                ctx.fill();
                ctx.strokeStyle = "rgba(255,255,255,0.15)";
                ctx.lineWidth = 0.5;
                ctx.stroke();

                if (globalScale > 0.7) {
                  ctx.font = `${fontSize}px sans-serif`;
                  ctx.textAlign = "center";
                  ctx.textBaseline = "top";
                  ctx.fillStyle = "#e2e8f0";
                  ctx.fillText(label, node.x, node.y + size + 1.5);
                }
              }}
              nodePointerAreaPaint={(node: any, color: string, ctx: CanvasRenderingContext2D) => {
                const size = Math.max(3, Math.sqrt(node.value ?? 4) * 2) + 2;
                ctx.beginPath();
                ctx.arc(node.x, node.y, size, 0, 2 * Math.PI);
                ctx.fillStyle = color;
                ctx.fill();
              }}
            />
          )}

          {selectedNode && (
            <div className="kg-panel-overlay">
              <div className="kg-panel-header">
                <h4 className="kg-panel-label">{selectedNode.label}</h4>
                <button
                  className="kg-panel-close"
                  onClick={() => setSelectedNode(null)}
                  aria-label="Close panel"
                >
                  ✕
                </button>
              </div>
              <div className="kg-panel-body">
                <div className="kg-panel-meta">
                  <span className="kg-panel-badge">{selectedNode.type}</span>
                  <span className="kg-panel-badge">
                    value: {selectedNode.value}
                  </span>
                  <span
                    className="kg-panel-badge"
                    style={{
                      background: `${selectedNode.color}33`,
                      color: selectedNode.color,
                    }}
                  >
                    {selectedNode.clusterName}
                  </span>
                </div>

                {selectedNode.context && (
                  <>
                    <h5 className="kg-panel-section-title">Context</h5>
                    <p className="kg-panel-context">{selectedNode.context}</p>
                  </>
                )}

                {selectedNode.insights.length > 0 && (
                  <>
                    <h5 className="kg-panel-section-title">Insights</h5>
                    <ul className="kg-panel-insights">
                      {selectedNode.insights.map((insight, i) => (
                        <li key={i}>{insight}</li>
                      ))}
                    </ul>
                  </>
                )}
              </div>
            </div>
          )}
        </div>
      </>
    );
  }
}
