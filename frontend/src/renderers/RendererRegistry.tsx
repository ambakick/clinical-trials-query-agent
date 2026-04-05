import type { ComponentType } from "react";
import type { SelectionState, VisualizationSpec } from "../types/api";
import { BarChartRenderer } from "./BarChartRenderer";
import { GroupedBarChartRenderer } from "./GroupedBarChartRenderer";
import { NetworkGraphRenderer } from "./NetworkGraphRenderer";
import { PieChartRenderer } from "./PieChartRenderer";
import { ScatterPlotRenderer } from "./ScatterPlotRenderer";
import { TimeSeriesRenderer } from "./TimeSeriesRenderer";

type RendererProps = {
  visualization: VisualizationSpec;
  onSelect: (selection: SelectionState | null) => void;
};

export const rendererRegistry: Record<VisualizationSpec["type"], ComponentType<RendererProps>> = {
  bar_chart: BarChartRenderer,
  grouped_bar_chart: GroupedBarChartRenderer,
  time_series: TimeSeriesRenderer,
  network_graph: NetworkGraphRenderer,
  pie_chart: PieChartRenderer,
  scatter_plot: ScatterPlotRenderer,
};
