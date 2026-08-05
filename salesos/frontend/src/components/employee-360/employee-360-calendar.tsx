"use client";

import { useCalendarKPIs } from "@/lib/hooks/employeeQueries";
import { Card, CardContent, CardHeader, Skeleton, Badge, cn } from "@salesos/ui";
import { Calendar, Clock, Users, TrendingUp, Video } from "lucide-react";

function KPICard({
  label,
  value,
  sub,
  icon: Icon,
  color,
}: {
  label: string;
  value: string | number;
  sub?: string;
  icon: React.ElementType;
  color: string;
}) {
  return (
    <div className={cn("rounded-xl border p-4", color)}>
      <div className="flex items-center justify-between mb-2">
        <span className="text-xs font-medium text-[var(--text-muted)]">{label}</span>
        <Icon className="h-4 w-4 opacity-50" />
      </div>
      <p className="text-2xl font-bold text-[var(--text-primary)]">{value}</p>
      {sub && <p className="text-xs text-[var(--text-muted)] mt-0.5">{sub}</p>}
    </div>
  );
}

export function CalendarDashboard({ employeeId }: { employeeId: string }) {
  const { data: kpis, isLoading: kpisLoading } = useCalendarKPIs(employeeId);

  if (kpisLoading) {
    return (
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        {Array.from({ length: 8 }).map((_, i) => (
          <Skeleton key={i} className="h-24 rounded-xl" />
        ))}
      </div>
    );
  }

  if (!kpis) return null;

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <KPICard
          label="Today"
          value={kpis.today_count}
          sub="meetings"
          icon={Calendar}
          color="bg-blue-50 dark:bg-blue-900/20 border-blue-200 dark:border-blue-800"
        />
        <KPICard
          label="This Week"
          value={kpis.week_count}
          sub="meetings"
          icon={Calendar}
          color="bg-purple-50 dark:bg-purple-900/20 border-purple-200 dark:border-purple-800"
        />
        <KPICard
          label="This Month"
          value={kpis.month_count}
          sub="meetings"
          icon={Calendar}
          color="bg-indigo-50 dark:bg-indigo-900/20 border-indigo-200 dark:border-indigo-800"
        />
        <KPICard
          label="Total Hours"
          value={`${kpis.total_hours}h`}
          sub={`${kpis.avg_duration_minutes}min avg`}
          icon={Clock}
          color="bg-amber-50 dark:bg-amber-900/20 border-amber-200 dark:border-amber-800"
        />
        <KPICard
          label="Focus Time"
          value={`${kpis.focus_time_hours}h`}
          sub="available"
          icon={Users}
          color="bg-green-50 dark:bg-green-900/20 border-green-200 dark:border-green-800"
        />
        <KPICard
          label="Utilization"
          value={`${kpis.calendar_utilization}%`}
          icon={TrendingUp}
          color="bg-teal-50 dark:bg-teal-900/20 border-teal-200 dark:border-teal-800"
        />
        <KPICard
          label="Internal"
          value={kpis.internal_count}
          sub="meetings"
          icon={Users}
          color="bg-slate-50 dark:bg-slate-900/20 border-slate-200 dark:border-slate-800"
        />
        <KPICard
          label="External"
          value={kpis.external_count}
          sub={`${kpis.cancellation_rate}% cancelled`}
          icon={Video}
          color="bg-orange-50 dark:bg-orange-900/20 border-orange-200 dark:border-orange-800"
        />
      </div>

      {kpis.upcoming.length > 0 && (
        <Card>
          <CardHeader>
            <h3 className="text-sm font-semibold">Upcoming Meetings</h3>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {kpis.upcoming.map((m, i) => (
                <div
                  key={i}
                  className="flex items-center gap-3 p-2 rounded-lg bg-[var(--bg-secondary)]"
                >
                  <Badge variant={m.is_internal ? "default" : "primary"} className="text-[10px]">
                    {m.is_internal ? "Internal" : "External"}
                  </Badge>
                  <span className="text-sm font-medium flex-1">{m.title}</span>
                  <span className="text-xs text-[var(--text-muted)]">
                    {new Date(m.start).toLocaleDateString("en-US", {
                      weekday: "short",
                      month: "short",
                      day: "numeric",
                      hour: "2-digit",
                      minute: "2-digit",
                    })}
                  </span>
                  <span className="text-xs text-[var(--text-disabled)]">
                    {m.attendees_count} attendees
                  </span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
