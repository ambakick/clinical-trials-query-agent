import {
  CartesianGrid,
  ResponsiveContainer,
  Scatter,
  ScatterChart,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { SelectionState, VisualizationSpec } from "../types/api";
import { createDatumSelection } from "../lib/selection";

type RendererProps = {
  visualization: VisualizationSpec;
  onSelect: (selection: SelectionState | null) => void;
};

export function ScatterPlotRenderer({ visualization, onSelect }: RendererProps) {
  const data = Array.isArray(visualization.data) ? visualization.data : [];
  const x = visualization.encoding.x;
  const y = visualization.encoding.y;

  return (
    <div className="chart-surface" data-testid="scatter-plot-renderer">
      <ResponsiveContainer width="100%" height={420}>
        <ScatterChart
          margin={{ top: 16, right: 16, bottom: 24, left: 0 }}
          onClick={(state) => {
            const datum = state?.activePayload?.[0]?.payload;
            if (datum) {
              const title = typeof datum.title === "string" ? datum.title : String(datum.nct_id ?? "Study");
              onSelect(
                createDatumSelection(
                  datum,
                  title,
                  `${x.title ?? x.field}: ${datum[x.field]} • ${y.title ?? y.field}: ${datum[y.field]}`,
                ),
              );
            }
          }}
        >
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis type="number" dataKey={x.field} name={x.title ?? x.field} tickLine={false} axisLine={false} />
          <YAxis type="number" dataKey={y.field} name={y.title ?? y.field} tickLine={false} axisLine={false} />
          <Tooltip cursor={{ strokeDasharray: "3 3" }} />
          <Scatter data={data} fill="#5f3dc4" />
        </ScatterChart>
      </ResponsiveContainer>
    </div>
  );
}
