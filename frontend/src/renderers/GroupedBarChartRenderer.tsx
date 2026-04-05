import { useMemo } from "react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
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

const palette = ["#1864ab", "#9c36b5", "#e8590c", "#2b8a3e", "#c92a2a"];

export function GroupedBarChartRenderer({ visualization, onSelect }: RendererProps) {
  const data = Array.isArray(visualization.data) ? visualization.data : [];
  const x = visualization.encoding.x;
  const y = visualization.encoding.y;
  const series = visualization.encoding.series;

  const { pivoted, seriesValues, originalMap } = useMemo(() => {
    const byCategory = new Map<string, Record<string, unknown>>();
    const originals = new Map<string, Record<string, unknown>>();
    const groups = new Set<string>();

    for (const row of data) {
      const category = String(row[x.field] ?? "Unknown");
      const cohort = String(row[series.field] ?? "Series");
      groups.add(cohort);
      originals.set(`${category}::${cohort}`, row);
      if (!byCategory.has(category)) {
        byCategory.set(category, { [x.field]: category });
      }
      byCategory.get(category)![cohort] = row[y.field];
    }

    return {
      pivoted: Array.from(byCategory.values()),
      seriesValues: Array.from(groups.values()),
      originalMap: originals,
    };
  }, [data, series.field, x.field, y.field]);

  return (
    <div className="chart-surface" data-testid="grouped-bar-chart-renderer">
      <ResponsiveContainer width="100%" height={420}>
        <BarChart data={pivoted} margin={{ top: 16, right: 16, bottom: 24, left: 0 }}>
          <CartesianGrid strokeDasharray="3 3" vertical={false} />
          <XAxis dataKey={x.field} tickLine={false} axisLine={false} height={60} />
          <YAxis tickLine={false} axisLine={false} />
          <Tooltip />
          <Legend />
          {seriesValues.map((value, index) => (
            <Bar
              key={value}
              dataKey={value}
              fill={palette[index % palette.length]}
              radius={[6, 6, 0, 0]}
              onClick={(payload) => {
                if (!payload?.payload) {
                  return;
                }
                const category = String(payload.payload[x.field]);
                const original = originalMap.get(`${category}::${value}`);
                if (original) {
                  onSelect(createDatumSelection(original, `${category}`, `${value} • ${y.title ?? y.field}: ${original[y.field]}`));
                }
              }}
            />
          ))}
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
