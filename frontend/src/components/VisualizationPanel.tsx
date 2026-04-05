import type { QueryResponse, SelectionState } from "../types/api";
import { rendererRegistry } from "../renderers/RendererRegistry";

type VisualizationPanelProps = {
  response: QueryResponse;
  onSelect: (selection: SelectionState | null) => void;
};

function hasNoData(response: QueryResponse): boolean {
  const { data } = response.visualization;
  if (Array.isArray(data)) {
    return data.length === 0;
  }
  return data.nodes.length === 0 && data.edges.length === 0;
}

export function VisualizationPanel({ response, onSelect }: VisualizationPanelProps) {
  const Renderer = rendererRegistry[response.visualization.type];

  return (
    <section className="visualization-panel">
      <div className="visualization-panel__header">
        <div>
          <p className="eyebrow">Visualization</p>
          <h2>{response.visualization.title}</h2>
          {response.visualization.description ? <p>{response.visualization.description}</p> : null}
        </div>
      </div>
      {hasNoData(response) ? (
        <div className="visualization-panel__empty">
          <p>No rows matched the compiled query after filtering.</p>
          <p>Adjust the question or filters and try again.</p>
        </div>
      ) : (
        <Renderer visualization={response.visualization} onSelect={onSelect} />
      )}
    </section>
  );
}
