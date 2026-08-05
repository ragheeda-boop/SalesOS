import { cn } from "@salesos/ui";
import {
  BarChart as RechartsBarChart,
  Bar,
  LineChart as RechartsLineChart,
  Line,
  PieChart as RechartsPieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from "recharts";

export interface ChartDataPoint {
  label: string;
  value: number;
  color?: string;
}

export interface ChartProps {
  title?: string;
  className?: string;
  height?: number;
}

const COLORS = [
  "#F57C1E", // orange — primary brand
  "#22C55E", // green — success
  "#F59E0B", // amber — warning
  "#EF4444", // red — danger
  "#A855F7", // purple — ai/copilot
  "#3B82F6", // blue — info
  "#F97316", // orange-700
  "#16A34A", // green-700
];

export function BarChart({
  data,
  title,
  className,
  height = 200,
}: { data: ChartDataPoint[] } & ChartProps) {
  return (
    <div className={cn("space-y-2", className)}>
      {title && (
        <h4 className="text-sm font-medium" style={{ color: "var(--text-primary)" }}>
          {title}
        </h4>
      )}
      <ResponsiveContainer width="100%" height={height}>
        <RechartsBarChart data={data}>
          <CartesianGrid strokeDasharray="3 3" className="stroke-[var(--border-default)]" />
          <XAxis dataKey="label" tick={{ fontSize: 10 }} style={{ color: "var(--text-muted)" }} />
          <YAxis tick={{ fontSize: 10 }} style={{ color: "var(--text-muted)" }} />
          <Tooltip />
          <Bar dataKey="value" radius={[4, 4, 0, 0]}>
            {data.map((entry, i) => (
              <Cell key={i} fill={entry.color || COLORS[i % COLORS.length]} />
            ))}
          </Bar>
        </RechartsBarChart>
      </ResponsiveContainer>
    </div>
  );
}

export function LineChart({
  series,
  title,
  className,
  height = 200,
}: { series: ChartSeries[] } & ChartProps) {
  const labels = series[0]?.data.map((_, i) => `P${i + 1}`) || [];
  const chartData = labels.map((label, i) => {
    const point: Record<string, string | number> = { label };
    series.forEach((s) => {
      point[s.name] = s.data[i];
    });
    return point;
  });
  return (
    <div className={cn("space-y-2", className)}>
      {title && (
        <h4 className="text-sm font-medium" style={{ color: "var(--text-primary)" }}>
          {title}
        </h4>
      )}
      <ResponsiveContainer width="100%" height={height}>
        <RechartsLineChart data={chartData}>
          <CartesianGrid strokeDasharray="3 3" className="stroke-[var(--border-default)]" />
          <XAxis dataKey="label" tick={{ fontSize: 10 }} style={{ color: "var(--text-muted)" }} />
          <YAxis tick={{ fontSize: 10 }} style={{ color: "var(--text-muted)" }} />
          <Tooltip />
          <Legend />
          {series.map((s, i) => (
            <Line
              key={s.name}
              type="monotone"
              dataKey={s.name}
              stroke={s.color || COLORS[i % COLORS.length]}
              strokeWidth={2}
              dot={false}
            />
          ))}
        </RechartsLineChart>
      </ResponsiveContainer>
    </div>
  );
}

export interface ChartSeries {
  name: string;
  color: string;
  data: number[];
}

export function PieChart({ data, title, className }: { data: ChartDataPoint[] } & ChartProps) {
  return (
    <div className={cn("space-y-2", className)}>
      {title && (
        <h4 className="text-sm font-medium" style={{ color: "var(--text-primary)" }}>
          {title}
        </h4>
      )}
      <ResponsiveContainer width="100%" height={200}>
        <RechartsPieChart>
          <Pie
            data={data}
            dataKey="value"
            nameKey="label"
            cx="50%"
            cy="50%"
            outerRadius={70}
            label={({ label, percent }) => `${label} ${(percent * 100).toFixed(0)}%`}
          >
            {data.map((entry, i) => (
              <Cell key={i} fill={entry.color || COLORS[i % COLORS.length]} />
            ))}
          </Pie>
          <Tooltip />
        </RechartsPieChart>
      </ResponsiveContainer>
    </div>
  );
}

export function MetricCard({
  label,
  value,
  trend,
  icon,
  className,
}: {
  label: string;
  value: string;
  trend?: { direction: "up" | "down"; percentage: number };
  icon?: React.ReactNode;
  className?: string;
}) {
  return (
    <div
      className={cn("rounded-xl border p-4 shadow-sm", className)}
      style={{ background: "var(--bg-primary)", borderColor: "var(--border-default)" }}
    >
      <div className="flex items-center justify-between">
        <span className="text-sm" style={{ color: "var(--text-muted)" }}>
          {label}
        </span>
        {icon && <span style={{ color: "var(--text-muted)" }}>{icon}</span>}
      </div>
      <div className="mt-2 flex items-baseline gap-2">
        <span className="text-2xl font-semibold" style={{ color: "var(--text-primary)" }}>
          {value}
        </span>
        {trend && (
          <span
            className={cn("text-xs font-medium")}
            style={{
              color:
                trend.direction === "up" ? "var(--muhide-orange)" : "var(--danger-600, #EF4444)",
            }}
          >
            {trend.direction === "up" ? "↑" : "↓"} {trend.percentage}%
          </span>
        )}
      </div>
    </div>
  );
}
