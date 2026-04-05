import {
  Bar,
  BarChart,
  CartesianGrid,
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

export function BarChartRenderer({ visualization, onSelect }: RendererProps) {
  const data = Array.isArray(visualization.data) ? visualization.data : [];
  const x = visualization.encoding.x;
  const y = visualization.encoding.y;

  return (
    <div className="chart-surface" data-testid="bar-chart-renderer">
      <ResponsiveContainer width="100%" height={420}>
        <BarChart data={data} margin={{ top: 16, right: 16, bottom: 24, left: 0 }}>
          <CartesianGrid strokeDasharray="3 3" vertical={false} />
          <XAxis dataKey={x.field} tickLine={false} axisLine={false} height={60} angle={data.length > 12 ? -25 : 0} textAnchor="end" />
          <YAxis tickLine={false} axisLine={false} />
          <Tooltip />
          <Bar
            dataKey={y.field}
            fill="#1864ab"
            radius={[8, 8, 0, 0]}
            onClick={(payload) => {
              if (payload && payload.payload) {
                onSelect(createDatumSelection(payload.payload, `${payload.payload[x.field]}`, `${y.title ?? y.field}: ${payload.payload[y.field]}`));
              }
            }}
          />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
