import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
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

export function TimeSeriesRenderer({ visualization, onSelect }: RendererProps) {
  const data = Array.isArray(visualization.data) ? visualization.data : [];
  const x = visualization.encoding.x;
  const y = visualization.encoding.y;

  return (
    <div className="chart-surface" data-testid="time-series-renderer">
      <ResponsiveContainer width="100%" height={420}>
        <LineChart
          data={data}
          margin={{ top: 16, right: 16, bottom: 24, left: 0 }}
          onClick={(state) => {
            const datum = state?.activePayload?.[0]?.payload;
            if (datum) {
              onSelect(createDatumSelection(datum, `${datum[x.field]}`, `${y.title ?? y.field}: ${datum[y.field]}`));
            }
          }}
        >
          <CartesianGrid strokeDasharray="3 3" vertical={false} />
          <XAxis dataKey={x.field} tickLine={false} axisLine={false} />
          <YAxis tickLine={false} axisLine={false} />
          <Tooltip />
          <Line type="monotone" dataKey={y.field} stroke="#1c7ed6" strokeWidth={3} dot={{ r: 4 }} activeDot={{ r: 7 }} />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
