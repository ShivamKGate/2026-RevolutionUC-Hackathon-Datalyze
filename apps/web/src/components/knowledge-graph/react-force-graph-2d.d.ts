declare module "react-force-graph-2d" {
  import { Component } from "react";
  interface ForceGraphProps {
    graphData?: { nodes: any[]; links: any[] };
    nodeLabel?: string | ((node: any) => string);
    nodeColor?: string | ((node: any) => string);
    nodeVal?: string | ((node: any) => number);
    linkLabel?: string | ((link: any) => string);
    linkWidth?: string | ((link: any) => number);
    linkColor?: string | ((link: any) => string);
    linkDirectionalParticles?: number;
    onNodeClick?: (node: any, event: MouseEvent) => void;
    backgroundColor?: string;
    width?: number;
    height?: number;
    [key: string]: any;
  }
  export default class ForceGraph2D extends Component<ForceGraphProps> {}
}
