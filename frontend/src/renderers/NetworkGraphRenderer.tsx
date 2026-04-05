import ForceGraph2D from "react-force-graph-2d";
import type { SelectionState, VisualizationSpec } from "../types/api";
import type { NetworkData, NetworkEdge, NetworkNode } from "../types/api";
import { createEdgeSelection, createNodeSelection } from "../lib/selection";

type RendererProps = {
  visualization: VisualizationSpec;
  onSelect: (selection: SelectionState | null) => void;
};

const nodePalette: Record<string, string> = {
  sponsor: "#d9480f",
  drug: "#1864ab",
  condition: "#2b8a3e",
};

export function NetworkGraphRenderer({ visualization, onSelect }: RendererProps) {
  const data = visualization.data as NetworkData;
  const nodeLabels = new Map(data.nodes.map((node) => [node.id, node.label]));
  const graphData = {
    nodes: data.nodes,
    links: data.edges,
  };

  return (
    <div className="network-shell" data-testid="network-graph-renderer">
      <div className="network-shell__graph">
        <ForceGraph2D
          graphData={graphData}
          nodeAutoColorBy="type"
          nodeLabel={(node) => `${(node as NetworkNode).label} (${(node as NetworkNode).type})`}
          linkLabel={(edge) => `${nodeLabels.get((edge as NetworkEdge).source)} → ${nodeLabels.get((edge as NetworkEdge).target)} • ${(edge as NetworkEdge).weight}`}
          nodeVal={(node) => Math.max(4, Math.sqrt((node as NetworkNode).size))}
          linkWidth={(edge) => Math.max(1, Math.log2((edge as NetworkEdge).weight + 1))}
          nodeCanvasObject={(node, ctx, globalScale) => {
            const typedNode = node as NetworkNode & { x?: number; y?: number };
            const label = typedNode.label;
            const size = Math.max(4, Math.sqrt(typedNode.size));
            const fontSize = Math.max(10 / globalScale, 3);
            ctx.beginPath();
            ctx.fillStyle = nodePalette[typedNode.type] ?? "#495057";
            ctx.arc(typedNode.x ?? 0, typedNode.y ?? 0, size, 0, 2 * Math.PI, false);
            ctx.fill();
            ctx.font = `${fontSize}px sans-serif`;
            ctx.fillStyle = "#1f2933";
            ctx.fillText(label, (typedNode.x ?? 0) + size + 2, (typedNode.y ?? 0) + fontSize / 3);
          }}
          onNodeClick={(node) => onSelect(createNodeSelection(node as NetworkNode))}
          onLinkClick={(edge) =>
            onSelect(
              createEdgeSelection(
                edge as NetworkEdge,
                nodeLabels.get((edge as NetworkEdge).source),
                nodeLabels.get((edge as NetworkEdge).target),
              ),
            )
          }
        />
      </div>
      <div className="network-shell__table">
        <h3>Edges</h3>
        <div className="network-shell__rows">
          {data.edges.slice(0, 24).map((edge) => (
            <button
              key={`${edge.source}-${edge.target}`}
              type="button"
              className="network-shell__row"
              onClick={() =>
                onSelect(createEdgeSelection(edge, nodeLabels.get(edge.source), nodeLabels.get(edge.target)))
              }
            >
              <span>{nodeLabels.get(edge.source)}</span>
              <span>{nodeLabels.get(edge.target)}</span>
              <strong>{edge.weight}</strong>
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}
