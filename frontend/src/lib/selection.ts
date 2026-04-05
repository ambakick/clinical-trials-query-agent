import type { Citation, NetworkEdge, NetworkNode, SelectionState } from "../types/api";

type GenericDatum = Record<string, unknown> & { citations?: Citation[] };

export function getDatumCitations(datum: Record<string, unknown>): Citation[] {
  if (Array.isArray((datum as GenericDatum).citations)) {
    return (datum as GenericDatum).citations ?? [];
  }
  return [];
}

export function createDatumSelection(
  datum: Record<string, unknown>,
  title: string,
  subtitle?: string,
): SelectionState {
  return {
    kind: "datum",
    title,
    subtitle,
    citations: getDatumCitations(datum),
    payload: datum,
  };
}

export function createNodeSelection(node: NetworkNode): SelectionState {
  return {
    kind: "node",
    title: node.label,
    subtitle: `${node.type} node`,
    citations: [],
    payload: node as unknown as Record<string, unknown>,
  };
}

export function createEdgeSelection(edge: NetworkEdge, sourceLabel?: string, targetLabel?: string): SelectionState {
  return {
    kind: "edge",
    title: `${sourceLabel ?? edge.source} → ${targetLabel ?? edge.target}`,
    subtitle: `Weight ${edge.weight}`,
    citations: edge.citations ?? [],
    payload: edge as unknown as Record<string, unknown>,
  };
}
