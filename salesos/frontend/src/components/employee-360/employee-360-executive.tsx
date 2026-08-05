"use client";

import { useExecutiveSummary } from "@/lib/hooks/employeeQueries";
import { Card, CardContent, CardHeader, Skeleton, Badge } from "@salesos/ui";
import {
  Users,
  TrendingUp,
  Activity,
  AlertTriangle,
  UserPlus,
  Building2,
  Star,
} from "lucide-react";

export function ExecutiveCockpit() {
  const { data, isLoading } = useExecutiveSummary();

  if (isLoading) {
    return (
      <div className="space-y-4">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          {Array.from({ length: 6 }).map((_, i) => (
            <Skeleton key={i} className="h-28 rounded-xl" />
          ))}
        </div>
      </div>
    );
  }

  if (!data) return null;

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-3">
        <MetricCard
          label="Total Employees"
          value={data.total_employees}
          icon={Users}
          color="bg-blue-50 dark:bg-blue-900/20"
        />
        <MetricCard
          label="Active"
          value={data.active_employees}
          icon={Activity}
          color="bg-green-50 dark:bg-green-900/20"
        />
        <MetricCard
          label="New This Month"
          value={data.new_this_month}
          icon={UserPlus}
          color="bg-purple-50 dark:bg-purple-900/20"
        />
        <MetricCard
          label="Avg Score"
          value={`${data.avg_score}/100`}
          icon={Star}
          color="bg-amber-50 dark:bg-amber-900/20"
        />
        <MetricCard
          label="Signals (30d)"
          value={data.total_signals_30d}
          icon={TrendingUp}
          color="bg-teal-50 dark:bg-teal-900/20"
        />
        <MetricCard
          label="At Risk"
          value={data.at_risk_count}
          icon={AlertTriangle}
          color={
            data.at_risk_count > 0
              ? "bg-red-50 dark:bg-red-900/20"
              : "bg-green-50 dark:bg-green-900/20"
          }
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <Card>
          <CardHeader>
            <h3 className="text-sm font-semibold flex items-center gap-2">
              <Building2 className="h-4 w-4" /> Departments
            </h3>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {data.departments.map((d, i) => (
                <div key={i} className="flex items-center justify-between text-sm">
                  <span className="text-[var(--text-secondary)]">{d.name}</span>
                  <span className="font-medium">{d.headcount}</span>
                  <div className="flex-1 mx-3 h-2 rounded-full bg-[var(--bg-tertiary)] max-w-[200px]">
                    <div
                      className="h-full rounded-full bg-[var(--muhide-orange)]"
                      style={{
                        width: `${(d.headcount / Math.max(1, data.total_employees)) * 100}%`,
                      }}
                    />
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <h3 className="text-sm font-semibold flex items-center gap-2">
              <Star className="h-4 w-4" /> Top Performers
            </h3>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {data.top_performers.map((p, i) => (
                <div key={i} className="flex items-center gap-3 text-sm">
                  <span
                    className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold ${
                      i === 0
                        ? "bg-yellow-400 text-white"
                        : i === 1
                          ? "bg-slate-300 text-white"
                          : i === 2
                            ? "bg-amber-600 text-white"
                            : "bg-[var(--bg-tertiary)] text-[var(--text-muted)]"
                    }`}
                  >
                    {i + 1}
                  </span>
                  <span className="flex-1 text-[var(--text-primary)]">{p.name}</span>
                  <span className="text-xs text-[var(--text-muted)]">{p.department || p.role}</span>
                  <Badge
                    variant={p.score >= 70 ? "success" : p.score >= 40 ? "warning" : "danger"}
                    className="text-[10px]"
                  >
                    {p.score}
                  </Badge>
                </div>
              ))}
              {data.top_performers.length === 0 && (
                <p className="text-xs text-[var(--text-disabled)]">No scores recorded yet</p>
              )}
            </div>
          </CardContent>
        </Card>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Card>
          <CardHeader>
            <h3 className="text-sm font-semibold">Roles Breakdown</h3>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {data.roles.map((r, i) => (
                <div key={i} className="flex items-center justify-between text-sm">
                  <span className="text-[var(--text-secondary)] capitalize">
                    {r.role.replace(/_/g, " ")}
                  </span>
                  <span className="font-medium">{r.count}</span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <h3 className="text-sm font-semibold">Status Overview</h3>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="flex items-center justify-between text-sm">
              <span>Active Rate</span>
              <span className="font-medium">
                {data.total_employees > 0
                  ? Math.round((data.active_employees / data.total_employees) * 100)
                  : 0}
                %
              </span>
            </div>
            <div className="flex items-center justify-between text-sm">
              <span>New Hire Rate</span>
              <span className="font-medium">
                {data.total_employees > 0
                  ? Math.round((data.new_this_month / data.total_employees) * 100)
                  : 0}
                %
              </span>
            </div>
            <div className="flex items-center justify-between text-sm">
              <span>At-Risk Rate</span>
              <span
                className={`font-medium ${data.at_risk_count > 0 ? "text-danger-600" : "text-success-600"}`}
              >
                {data.total_employees > 0
                  ? Math.round((data.at_risk_count / data.total_employees) * 100)
                  : 0}
                %
              </span>
            </div>
            <p className="text-[10px] text-[var(--text-disabled)] pt-2">
              Generated: {new Date(data.generated_at).toLocaleString()}
            </p>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

function MetricCard({
  label,
  value,
  icon: Icon,
  color,
}: {
  label: string;
  value: number | string;
  icon: React.ElementType;
  color: string;
}) {
  return (
    <div className={`rounded-xl border p-4 ${color}`}>
      <div className="flex items-center justify-between mb-2">
        <span className="text-xs font-medium text-[var(--text-muted)]">{label}</span>
        <Icon className="h-4 w-4 opacity-50" />
      </div>
      <p className="text-2xl font-bold text-[var(--text-primary)]">{value}</p>
    </div>
  );
}
