import { Cell, Legend, Pie, PieChart, ResponsiveContainer, Tooltip } from "recharts";
import type { SelectionState, VisualizationSpec } from "../types/api";
import { createDatumSelection } from "../lib/selection";

type RendererProps = {
  visualization: VisualizationSpec;
  onSelect: (selection: SelectionState | null) => void;
};

const palette = ["#1864ab", "#9c36b5", "#e8590c", "#2b8a3e", "#c92a2a", "#d9480f", "#495057"];

export function PieChartRenderer({ visualization, onSelect }: RendererProps) {
  const data = Array.isArray(visualization.data) ? visualization.data : [];
  const x = visualization.encoding.x;
  const y = visualization.encoding.y;

  return (
    <div className="chart-surface" data-testid="pie-chart-renderer">
      <ResponsiveContainer width="100%" height={420}>
        <PieChart>
          <Pie
            data={data}
            dataKey={y.field}
            nameKey={x.field}
            outerRadius={150}
            innerRadius={72}
            paddingAngle={2}
            onClick={(payload) => {
              if (payload?.payload) {
                onSelect(createDatumSelection(payload.payload, `${payload.payload[x.field]}`, `${y.title ?? y.field}: ${payload.payload[y.field]}`));
              }
            }}
          >
            {data.map((row, index) => (
              <Cell key={String(row[x.field] ?? index)} fill={palette[index % palette.length]} />
            ))}
          </Pie>
          <Tooltip />
          <Legend />
        </PieChart>
      </ResponsiveContainer>
    </div>
  );
}
