import { useMemo, useRef, type ReactNode } from "react";
import { Canvas, useFrame } from "@react-three/fiber";
import { Line, OrbitControls, Text } from "@react-three/drei";
import * as THREE from "three";
import type { Line2 } from "three-stdlib";
import type { KnowledgeGraphOutput, KGNode } from "../types";
import type { OrchEdge, OrchNode } from "./buildOrchestrationModel";

const KG_PALETTE = [
  "#2563eb",
  "#8b5cf6",
  "#06b6d4",
  "#f59e0b",
  "#10b981",
  "#ef4444",
  "#ec4899",
  "#f97316",
  "#14b8a6",
  "#6366f1",
];

const MAX_KG_NODES = 96;

/** Agent node color from orchestrator / activity status (live + completed runs). */
function agentStatusColor(status: string | undefined): string {
  const s = (status ?? "").toLowerCase().trim();
  if (
    s.includes("fail") ||
    s === "error" ||
    s.includes("error") ||
    s.includes("fatal")
  ) {
    return "#f87171";
  }
  if (
    s === "completed" ||
    s === "done" ||
    s === "ok" ||
    s === "success" ||
    s === "complete" ||
    s === "finished"
  ) {
    return "#4ade80";
  }
  if (s === "skipped" || s === "cancelled" || s === "canceled") {
    return "#94a3b8";
  }
  return "#facc15";
}

function sampleKgNodes(all: KGNode[]): KGNode[] {
  if (all.length <= MAX_KG_NODES) return all;
  const step = all.length / MAX_KG_NODES;
  const out: KGNode[] = [];
  for (let i = 0; i < MAX_KG_NODES; i++) {
    const idx = Math.min(all.length - 1, Math.floor(i * step));
    out.push(all[idx]!);
  }
  return out;
}

function layoutKgKnowledgeSubtree(
  kg: KnowledgeGraphOutput,
  hubPos: THREE.Vector3,
): {
  displayNodes: KGNode[];
  positions: Map<string, THREE.Vector3>;
  colors: Map<string, string>;
  displayEdges: { source: string; target: string }[];
} {
  const displayNodes = sampleKgNodes(kg.nodes);
  const idSet = new Set(displayNodes.map((n) => n.id));
  const clusterIdx = new Map<string, number>();
  kg.clusters.forEach((c, ci) => {
    for (const id of c.node_ids) {
      if (!clusterIdx.has(id)) clusterIdx.set(id, ci);
    }
  });
  const nClusters = Math.max(kg.clusters.length, 1);
  const positions = new Map<string, THREE.Vector3>();
  const colors = new Map<string, string>();

  displayNodes.forEach((node) => {
    const ci = clusterIdx.get(node.id) ?? 0;
    const color = KG_PALETTE[ci % KG_PALETTE.length]!;
    colors.set(node.id, color);
    const sector = (Math.PI * 2) / nClusters;
    const ang0 = ci * sector + sector * 0.12;
    const clusterIds =
      kg.clusters[ci]?.node_ids.filter((id) => idSet.has(id)) ?? [];
    const members = clusterIds.length ? clusterIds : [node.id];
    const idxInCluster = Math.max(members.indexOf(node.id), 0);
    const nM = Math.max(members.length, 1);
    const angSpan =
      nM <= 1 ? sector * 0.25 : (idxInCluster / (nM - 1)) * sector * 0.65;
    const ang = ang0 + angSpan;
    const ringR = 3.1 + (ci % 4) * 0.18;
    positions.set(
      node.id,
      new THREE.Vector3(
        hubPos.x + Math.cos(ang) * ringR,
        hubPos.y - 2.5,
        hubPos.z + Math.sin(ang) * ringR,
      ),
    );
  });

  const displayEdges = (kg.edges ?? []).filter(
    (e) => idSet.has(e.source) && idSet.has(e.target),
  );

  return { displayNodes, positions, colors, displayEdges };
}

/** Dashed Line2 with animated dashOffset for a subtle “data flow” look (KG edges only). */
function KgFlowLine({
  points,
  color,
  lineWidth,
  dashSize,
  gapSize,
  speed = 2.4,
  transparent,
  opacity,
  animate,
}: {
  points: [number, number, number][];
  color: string;
  lineWidth: number;
  dashSize: number;
  gapSize: number;
  speed?: number;
  transparent?: boolean;
  opacity?: number;
  animate: boolean;
}) {
  const ref = useRef<Line2 | null>(null);
  useFrame((_, dt) => {
    if (!animate) return;
    const m = ref.current?.material as { dashOffset?: number } | undefined;
    if (m && typeof m.dashOffset === "number") {
      m.dashOffset -= dt * speed;
    }
  });
  return (
    <Line
      ref={ref}
      points={points}
      color={color}
      lineWidth={lineWidth}
      dashed
      dashSize={dashSize}
      gapSize={gapSize}
      transparent={Boolean(transparent)}
      opacity={opacity ?? 1}
    />
  );
}

function KnowledgeGraph3DLayer({
  kg,
  hubPos,
  animateFlow,
}: {
  kg: KnowledgeGraphOutput;
  hubPos: THREE.Vector3;
  animateFlow: boolean;
}) {
  const layout = useMemo(
    () => layoutKgKnowledgeSubtree(kg, hubPos),
    [kg, hubPos.x, hubPos.y, hubPos.z],
  );

  const hubLinks = layout.displayNodes.slice(0, 40);

  return (
    <>
      {layout.displayNodes.map((n) => {
        const p = layout.positions.get(n.id);
        const col = layout.colors.get(n.id) ?? "#94a3b8";
        if (!p) return null;
        return (
          <group key={`kg-node-${n.id}`} position={[p.x, p.y, p.z]}>
            <mesh>
              <sphereGeometry args={[0.11, 14, 14]} />
              <meshStandardMaterial color={col} />
            </mesh>
            <Text
              position={[0, 0.22, 0]}
              fontSize={0.12}
              color="#cbd5e1"
              anchorX="center"
              anchorY="bottom"
              maxWidth={1.5}
            >
              {n.label.length > 18 ? `${n.label.slice(0, 16)}…` : n.label}
            </Text>
          </group>
        );
      })}
      {layout.displayEdges.map((e, i) => {
        const a = layout.positions.get(e.source);
        const b = layout.positions.get(e.target);
        if (!a || !b) return null;
        const pts: [number, number, number][] = [
          a.toArray() as [number, number, number],
          b.toArray() as [number, number, number],
        ];
        return (
          <KgFlowLine
            key={`kg-edge-${e.source}-${e.target}-${i}`}
            points={pts}
            color="#64748b"
            lineWidth={1.1}
            dashSize={0.11}
            gapSize={0.07}
            speed={2.2}
            animate={animateFlow}
          />
        );
      })}
      {hubLinks.map((n) => {
        const p = layout.positions.get(n.id);
        if (!p) return null;
        const pts: [number, number, number][] = [
          hubPos.toArray() as [number, number, number],
          p.toArray() as [number, number, number],
        ];
        return (
          <KgFlowLine
            key={`kg-hub-${n.id}`}
            points={pts}
            color="#22d3ee"
            lineWidth={1}
            dashSize={0.1}
            gapSize={0.07}
            speed={2.8}
            transparent
            opacity={0.42}
            animate={animateFlow}
          />
        );
      })}
    </>
  );
}

function layoutPositions(
  nodes: OrchNode[],
  dispatchOrderByAgent?: Record<string, number>,
): Map<string, THREE.Vector3> {
  const m = new Map<string, THREE.Vector3>();
  const root = nodes.find((n) => n.kind === "orchestrator");
  if (root) m.set(root.id, new THREE.Vector3(0, 4.15, 0));

  const agents = nodes.filter((n) => n.kind === "agent");
  const nA = agents.length || 1;
  const hasOrder =
    dispatchOrderByAgent && Object.keys(dispatchOrderByAgent).length > 0;
  let maxOrd = 0;
  if (hasOrder) {
    for (const a of agents) {
      const k = a.agentKey ?? "";
      const v = dispatchOrderByAgent[k];
      if (typeof v === "number" && v > maxOrd) maxOrd = v;
    }
  }
  agents.forEach((a, i) => {
    const ang = (i / nA) * Math.PI * 2;
    const k = a.agentKey ?? "";
    let r: number;
    if (hasOrder) {
      const ord =
        k && dispatchOrderByAgent[k] !== undefined
          ? dispatchOrderByAgent[k]!
          : maxOrd + 1;
      const baseR = 2.05;
      const step = 0.34;
      r = baseR + ord * step;
    } else {
      r = 2.45;
    }
    m.set(a.id, new THREE.Vector3(Math.cos(ang) * r, 0.28, Math.sin(ang) * r));
  });

  const kg = nodes.find((n) => n.kind === "kg_hub");
  if (kg) {
    m.set(kg.id, new THREE.Vector3(0, -1.35, 1.25));
  }

  const insightNodes = nodes.filter((n) => n.kind === "insight");
  const nI = insightNodes.length;
  insightNodes.forEach((n, i) => {
    const t = nI <= 1 ? 0.5 : i / (nI - 1);
    const ang = -Math.PI * 0.62 + t * Math.PI * 1.24;
    const r = 2.05;
    m.set(
      n.id,
      new THREE.Vector3(Math.cos(ang) * r, 0.05, Math.sin(ang) * r + 1.35),
    );
  });

  const dataNodes = nodes.filter((n) => n.kind === "data");
  dataNodes.forEach((d, i) => {
    const ang = (i / Math.max(dataNodes.length, 1)) * Math.PI * 2 + 0.4;
    const r = 4.15;
    m.set(d.id, new THREE.Vector3(Math.cos(ang) * r, -2.85, Math.sin(ang) * r));
  });
  return m;
}

function edgeColor(kind: OrchEdge["kind"]): string {
  switch (kind) {
    case "kg":
      return "#38bdf8";
    case "insight_flow":
      return "#f472b6";
    case "provenance":
      return "#c084fc";
    default:
      return "#64748b";
  }
}

function buildFlowPolylines(
  nodes: OrchNode[],
  pos: Map<string, THREE.Vector3>,
): { id: string; points: THREE.Vector3[]; color: string }[] {
  const ig = pos.get("agent:insight_generation");
  const kg = pos.get("kg:hub");
  const out: { id: string; points: THREE.Vector3[]; color: string }[] = [];
  for (const n of nodes) {
    if (n.kind !== "insight") continue;
    const ip = pos.get(n.id);
    if (!ip) continue;
    const pts: THREE.Vector3[] = [];
    if (ig) {
      pts.push(ig.clone());
      pts.push(
        new THREE.Vector3()
          .lerpVectors(ig, ip, 0.4)
          .add(new THREE.Vector3(0, 0.35, 0)),
      );
    }
    pts.push(ip.clone());
    if (kg) {
      pts.push(
        new THREE.Vector3()
          .lerpVectors(ip, kg, 0.55)
          .add(new THREE.Vector3(0, 0.2, 0)),
      );
      pts.push(kg.clone());
    }
    if (pts.length >= 2) {
      out.push({
        id: `flow-${n.id}`,
        points: pts,
        color: "#f9a8d4",
      });
    }
  }
  return out;
}

function RotatingGroup({
  children,
  enabled,
}: {
  children: ReactNode;
  /** When false, scene does not auto-spin (clearer for live data that updates in place). */
  enabled: boolean;
}) {
  const ref = useRef<THREE.Group>(null);
  useFrame((_, dt) => {
    if (enabled && ref.current) ref.current.rotation.y += dt * 0.05;
  });
  return <group ref={ref}>{children}</group>;
}

function NodeBall({
  node,
  position,
  selected,
  onPick,
}: {
  node: OrchNode;
  position: THREE.Vector3;
  selected: boolean;
  onPick: (n: OrchNode) => void;
}) {
  const color =
    node.kind === "orchestrator"
      ? "#38bdf8"
      : node.kind === "agent"
        ? agentStatusColor(node.status)
        : node.kind === "kg_hub"
          ? "#22d3ee"
          : node.kind === "insight"
            ? "#f472b6"
            : "#a78bfa";
  const emissive = selected ? "#92400e" : "#000000";

  return (
    <group position={[position.x, position.y, position.z]}>
      <mesh
        onClick={(e) => {
          e.stopPropagation();
          onPick(node);
        }}
        onPointerOver={(e) => {
          e.stopPropagation();
          document.body.style.cursor = "pointer";
        }}
        onPointerOut={() => {
          document.body.style.cursor = "";
        }}
      >
        {node.kind === "kg_hub" ? (
          <octahedronGeometry args={[selected ? 0.62 : 0.52]} />
        ) : node.kind === "insight" ? (
          <sphereGeometry args={[selected ? 0.28 : 0.22, 20, 20]} />
        ) : (
          <sphereGeometry args={[selected ? 0.48 : 0.38, 28, 28]} />
        )}
        <meshStandardMaterial
          color={selected ? "#fbbf24" : color}
          emissive={emissive}
          emissiveIntensity={selected ? 0.4 : 0}
        />
      </mesh>
      <Text
        position={[0, node.kind === "kg_hub" ? 0.85 : 0.65, 0]}
        fontSize={node.kind === "insight" ? 0.2 : 0.26}
        color="#e2e8f0"
        anchorX="center"
        anchorY="bottom"
        maxWidth={3}
      >
        {node.label.length > 22 ? `${node.label.slice(0, 20)}…` : node.label}
      </Text>
    </group>
  );
}

function EdgeLines({
  edges,
  pos,
}: {
  edges: OrchEdge[];
  pos: Map<string, THREE.Vector3>;
}) {
  return (
    <>
      {edges.map((e, i) => {
        const a = pos.get(e.from);
        const b = pos.get(e.to);
        if (!a || !b) return null;
        return (
          <Line
            key={`${e.from}-${e.to}-${i}`}
            points={[a.toArray(), b.toArray()]}
            color={edgeColor(e.kind)}
            lineWidth={e.kind === "core" ? 1.2 : 2}
            dashed={e.kind === "provenance"}
            dashSize={0.15}
            gapSize={0.12}
          />
        );
      })}
    </>
  );
}

function FlowLines({
  flows,
}: {
  flows: { id: string; points: THREE.Vector3[]; color: string }[];
}) {
  return (
    <>
      {flows.map((f) => (
        <Line
          key={f.id}
          points={f.points.map((p) => p.toArray())}
          color={f.color}
          lineWidth={2.2}
          dashed
          dashSize={0.08}
          gapSize={0.06}
        />
      ))}
    </>
  );
}

type Props = {
  nodes: OrchNode[];
  edges: OrchEdge[];
  selectedId: string | null;
  highlightIds: Set<string>;
  onSelect: (n: OrchNode | null) => void;
  /** When set, agents with higher dispatch order sit farther from the orchestrator. */
  dispatchOrderByAgent?: Record<string, number>;
  /** Slow ambient rotation of the whole graph (default true). */
  autoRotate?: boolean;
  /** Change to force a new WebGL scene when live data advances (avoids stale meshes). */
  remountKey?: string;
  /** Full knowledge graph: rendered in 3D around the KG hub node when present. */
  knowledgeGraph?: KnowledgeGraphOutput | null;
};

function SceneInner({
  nodes,
  edges,
  selectedId,
  highlightIds,
  onSelect,
  dispatchOrderByAgent,
  autoRotate = true,
  knowledgeGraph,
}: Props) {
  const pos = useMemo(
    () => layoutPositions(nodes, dispatchOrderByAgent),
    [nodes, dispatchOrderByAgent],
  );
  const flows = useMemo(() => buildFlowPolylines(nodes, pos), [nodes, pos]);
  const kgHubPos = pos.get("kg:hub");
  const reduceMotion =
    typeof window !== "undefined" &&
    window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  return (
    <>
      <ambientLight intensity={0.5} />
      <directionalLight position={[8, 14, 8]} intensity={0.9} />
      <directionalLight
        position={[-5, 6, -4]}
        intensity={0.35}
        color="#94a3b8"
      />
      <RotatingGroup enabled={Boolean(autoRotate) && !reduceMotion}>
        <EdgeLines edges={edges} pos={pos} />
        <FlowLines flows={flows} />
        {nodes.map((n) => {
          const p = pos.get(n.id);
          if (!p) return null;
          const selected = selectedId === n.id || highlightIds.has(n.id);
          return (
            <NodeBall
              key={n.id}
              node={n}
              position={p}
              selected={selected}
              onPick={onSelect}
            />
          );
        })}
        {knowledgeGraph &&
          knowledgeGraph.nodes.length > 0 &&
          kgHubPos != null && (
            <KnowledgeGraph3DLayer
              kg={knowledgeGraph}
              hubPos={kgHubPos}
              animateFlow={!reduceMotion}
            />
          )}
      </RotatingGroup>
      <OrbitControls enableDamping dampingFactor={0.08} />
    </>
  );
}

export function OrchestrationGraph3D(props: Props) {
  const { remountKey, ...sceneProps } = props;
  return (
    <div className="orch-graph-canvas" aria-label="Orchestration 3D graph">
      <Canvas
        key={remountKey ?? "orch-canvas"}
        camera={{
          position: [0.35 * 1.1, 4.2 * 1.1, 11.2 * 1.1],
          fov: 48,
        }}
        gl={{ antialias: true, alpha: true }}
        onPointerMissed={() => props.onSelect(null)}
      >
        <SceneInner {...sceneProps} />
      </Canvas>
    </div>
  );
}
