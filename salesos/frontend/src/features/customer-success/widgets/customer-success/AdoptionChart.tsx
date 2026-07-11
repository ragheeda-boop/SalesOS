"use client"

interface AdoptionData {
  feature: string
  label: string
  user_count: number
  total_users: number
  adoption_pct: number
}

interface AdoptionChartProps {
  data: AdoptionData[]
}

const FEATURE_COLORS = [
  "bg-orange-500",
  "bg-blue-500",
  "bg-green-500",
  "bg-purple-500",
  "bg-pink-500",
  "bg-teal-500",
  "bg-amber-500",
  "bg-indigo-500",
  "bg-red-500",
  "bg-cyan-500",
  "bg-emerald-500",
]

export function AdoptionChart({ data }: AdoptionChartProps) {
  if (!data || data.length === 0) {
    return (
      <div className="flex items-center justify-center h-48 text-sm text-[var(--text-muted)]">
        لا توجد بيانات تبني متاحة
      </div>
    )
  }

  return (
    <div className="space-y-3" role="img" aria-label="مخطط تبني الميزات">
      {data.map((item, i) => (
        <div key={item.feature}>
          <div className="flex items-center justify-between text-sm mb-1">
            <span className="text-[var(--text-primary)]">{item.label}</span>
            <span className="text-xs text-[var(--text-muted)]">{item.adoption_pct.toFixed(0)}%</span>
          </div>
          <div className="h-4 bg-neutral-100 dark:bg-neutral-800 rounded-full overflow-hidden" role="progressbar" aria-valuenow={item.adoption_pct} aria-valuemin={0} aria-valuemax={100} aria-label={`${item.label}: ${item.adoption_pct.toFixed(0)}%`}>
            <div
              className={cn("h-full rounded-full transition-all duration-500", FEATURE_COLORS[i % FEATURE_COLORS.length])}
              style={{ width: `${item.adoption_pct}%` }}
            />
          </div>
        </div>
      ))}
    </div>
  )
}

function cn(...classes: (string | boolean | undefined | null)[]) {
  return classes.filter(Boolean).join(" ")
}
