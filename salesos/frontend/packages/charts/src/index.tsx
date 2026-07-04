import { cn } from '@salesos/ui'
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
} from 'recharts'

export interface ChartDataPoint {
  label: string
  value: number
  color?: string
}

export interface ChartProps {
  title?: string
  className?: string
  height?: number
}

const COLORS = ['#3B82F6', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6', '#EC4899', '#06B6D4', '#F97316']

export function BarChart({ data, title, className, height = 200 }: { data: ChartDataPoint[] } & ChartProps) {
  return (
    <div className={cn('space-y-2', className)}>
      {title && <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300">{title}</h4>}
      <ResponsiveContainer width="100%" height={height}>
        <RechartsBarChart data={data}>
          <CartesianGrid strokeDasharray="3 3" className="stroke-gray-200 dark:stroke-gray-700" />
          <XAxis dataKey="label" tick={{ fontSize: 10 }} className="text-gray-500" />
          <YAxis tick={{ fontSize: 10 }} className="text-gray-500" />
          <Tooltip />
          <Bar dataKey="value" radius={[4, 4, 0, 0]}>
            {data.map((entry, i) => (
              <Cell key={i} fill={entry.color || COLORS[i % COLORS.length]} />
            ))}
          </Bar>
        </RechartsBarChart>
      </ResponsiveContainer>
    </div>
  )
}

export function LineChart({ series, title, className, height = 200 }: { series: ChartSeries[] } & ChartProps) {
  const labels = series[0]?.data.map((_, i) => `P${i + 1}`) || []
  const chartData = labels.map((label, i) => {
    const point: Record<string, string | number> = { label }
    series.forEach((s) => { point[s.name] = s.data[i] })
    return point
  })
  return (
    <div className={cn('space-y-2', className)}>
      {title && <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300">{title}</h4>}
      <ResponsiveContainer width="100%" height={height}>
        <RechartsLineChart data={chartData}>
          <CartesianGrid strokeDasharray="3 3" className="stroke-gray-200 dark:stroke-gray-700" />
          <XAxis dataKey="label" tick={{ fontSize: 10 }} />
          <YAxis tick={{ fontSize: 10 }} />
          <Tooltip />
          <Legend />
          {series.map((s, i) => (
            <Line key={s.name} type="monotone" dataKey={s.name} stroke={s.color || COLORS[i % COLORS.length]} strokeWidth={2} dot={false} />
          ))}
        </RechartsLineChart>
      </ResponsiveContainer>
    </div>
  )
}

export interface ChartSeries {
  name: string
  color: string
  data: number[]
}

export function PieChart({ data, title, className }: { data: ChartDataPoint[] } & ChartProps) {
  return (
    <div className={cn('space-y-2', className)}>
      {title && <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300">{title}</h4>}
      <ResponsiveContainer width="100%" height={200}>
        <RechartsPieChart>
          <Pie data={data} dataKey="value" nameKey="label" cx="50%" cy="50%" outerRadius={70} label={({ label, percent }) => `${label} ${(percent * 100).toFixed(0)}%`}>
            {data.map((entry, i) => (
              <Cell key={i} fill={entry.color || COLORS[i % COLORS.length]} />
            ))}
          </Pie>
          <Tooltip />
        </RechartsPieChart>
      </ResponsiveContainer>
    </div>
  )
}

export function MetricCard({
  label,
  value,
  trend,
  icon,
  className,
}: {
  label: string
  value: string
  trend?: { direction: 'up' | 'down'; percentage: number }
  icon?: React.ReactNode
  className?: string
}) {
  return (
    <div className={cn('rounded-xl border bg-white p-4 shadow-sm dark:border-gray-700 dark:bg-gray-900', className)}>
      <div className="flex items-center justify-between">
        <span className="text-sm text-gray-500 dark:text-gray-400">{label}</span>
        {icon && <span className="text-gray-400">{icon}</span>}
      </div>
      <div className="mt-2 flex items-baseline gap-2">
        <span className="text-2xl font-semibold text-gray-900 dark:text-gray-100">{value}</span>
        {trend && (
          <span
            className={cn(
              'text-xs font-medium',
              trend.direction === 'up' ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'
            )}
          >
            {trend.direction === 'up' ? '↑' : '↓'} {trend.percentage}%
          </span>
        )}
      </div>
    </div>
  )
}
