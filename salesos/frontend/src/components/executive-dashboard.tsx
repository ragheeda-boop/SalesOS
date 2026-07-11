"use client";

import { useExecutiveDashboard } from "@/lib/hooks/executiveQueries";
import { Card, CardContent, CardHeader, Badge, cn } from "@salesos/ui";
import { formatNumber } from "@/lib/utils";
import {
  DollarSign, TrendingUp, Users, AlertTriangle, Activity,
  BarChart3, Target, Calendar, Building2, UserPlus, FileSignature,
  Shield, ArrowUp, ArrowDown
} from "lucide-react";

function KPICard({
  title, value, subtitle, icon: Icon, color, trend, trendUp
}: {
  title: string; value: string; subtitle?: string;
  icon: React.ElementType; color: string; trend?: number; trendUp?: boolean;
}) {
  return (
    <Card className="overflow-hidden">
      <CardContent className="p-5">
        <div className="flex items-start justify-between">
          <div className="space-y-1">
            <p className="text-xs font-medium text-neutral-500 dark:text-neutral-400">{title}</p>
            <p className="text-2xl font-bold text-neutral-900 dark:text-neutral-100">{value}</p>
            {subtitle && <p className="text-xs text-neutral-500 dark:text-neutral-400">{subtitle}</p>}
            {trend !== undefined && (
              <span className={cn("inline-flex items-center gap-0.5 text-xs", trendUp ? "text-success-600" : "text-danger-600")}>
                {trendUp ? <ArrowUp className="h-3 w-3" /> : <ArrowDown className="h-3 w-3" />}
                {trend}%
              </span>
            )}
          </div>
          <div className={cn("flex h-10 w-10 items-center justify-center rounded-xl", color)}>
            <Icon className="h-5 w-5 text-white" />
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

function ProgressBar({ value, max, label, color }: { value: number; max: number; label: string; color: string }) {
  const pct = max > 0 ? Math.min((value / max) * 100, 100) : 0;
  return (
    <div className="space-y-1">
      <div className="flex items-center justify-between text-xs">
        <span className="text-neutral-600 dark:text-neutral-400">{label}</span>
        <span className="font-medium text-neutral-900 dark:text-neutral-100">{formatNumber(value)}</span>
      </div>
      <div className="h-2 w-full overflow-hidden rounded-full bg-neutral-200 dark:bg-neutral-700">
        <div className={cn("h-full rounded-full transition-all", color)} style={{ width: `${pct}%` }} />
      </div>
    </div>
  );
}

export function ExecutiveDashboard() {
  const { data, isLoading } = useExecutiveDashboard();

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-4">
          {Array.from({ length: 4 }).map((_, i) => (
            <Card key={i}><CardContent className="p-5"><div className="h-20 animate-pulse rounded bg-neutral-200 dark:bg-neutral-700" /></CardContent></Card>
          ))}
        </div>
      </div>
    );
  }

  if (!data) {
    return (
      <div className="flex items-center justify-center py-20">
        <p className="text-neutral-500 dark:text-neutral-400">فشل تحميل البيانات</p>
      </div>
    );
  }

  const d = data;
  const healthColor = d.health.overall_health === "good" ? "text-success-600 bg-success-100" :
    d.health.overall_health === "warning" ? "text-warning-600 bg-warning-100" : "text-danger-600 bg-danger-100";

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-neutral-900 dark:text-neutral-100">لوحة القيادة التنفيذية</h1>
          <p className="mt-1 text-sm text-neutral-500 dark:text-neutral-400">نظرة شاملة على أداء المنصة والمؤشرات الرئيسية</p>
        </div>
        <div className={cn("inline-flex items-center gap-2 rounded-full px-3 py-1 text-xs font-medium", healthColor)}>
          <Shield className="h-3 w-3" />
          {d.health.overall_health === "good" ? "صحي" : d.health.overall_health === "warning" ? "تحذير" : "حرج"}
        </div>
      </div>

      {/* KPI Row */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <KPICard
          title="الإيرادات المسجلة"
          value={`${formatNumber(d.revenue.total_booked)} ر.س`}
          subtitle={`مستهدف: ${formatNumber(d.revenue.forecast)} ر.س`}
          icon={DollarSign}
          color="bg-success-600"
        />
        <KPICard
          title="قيمة الصفقات"
          value={`${formatNumber(d.revenue.total_pipeline)} ر.س`}
          subtitle={`المرجح: ${formatNumber(d.revenue.weighted_pipeline)} ر.س`}
          icon={TrendingUp}
          color="bg-info-600"
        />
        <KPICard
          title="الموظفين النشطين"
          value={`${d.team.active_employees} / ${d.team.total_employees}`}
          subtitle={`نسبة الفوز: ${Math.round(d.team.avg_win_rate * 100)}%`}
          icon={Users}
          color="bg-purple-600"
        />
        <KPICard
          title="مخاطر"
          value={String(d.risk.expiring_contracts + d.risk.stalled_deals)}
          subtitle={`عقود منتهية: ${d.risk.expiring_contracts} | صفقات متعثرة: ${d.risk.stalled_deals}`}
          icon={AlertTriangle}
          color="bg-danger-600"
        />
      </div>

      {/* Main Grid */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        {/* Pipeline Health */}
        <Card>
          <CardHeader>
            <div className="flex items-center gap-2">
              <BarChart3 className="h-5 w-5 text-info-600" />
              <h2 className="text-lg font-bold text-neutral-900 dark:text-neutral-100">صحة الصفقات</h2>
            </div>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div className="rounded-lg bg-info-50 p-3 dark:bg-info-900/20">
                <p className="text-xs text-info-600 dark:text-info-400">إجمالي الصفقات</p>
                <p className="text-xl font-bold text-neutral-900 dark:text-neutral-100">{d.pipeline.total_deals}</p>
              </div>
              <div className="rounded-lg bg-success-50 p-3 dark:bg-success-900/20">
                <p className="text-xs text-success-600 dark:text-success-400">الصفقات الرابحة</p>
                <p className="text-xl font-bold text-neutral-900 dark:text-neutral-100">{d.pipeline.won_deals}</p>
              </div>
              <div className="rounded-lg bg-danger-50 p-3 dark:bg-danger-900/20">
                <p className="text-xs text-danger-600 dark:text-danger-400">الصفقات الخاسرة</p>
                <p className="text-xl font-bold text-neutral-900 dark:text-neutral-100">{d.pipeline.lost_deals}</p>
              </div>
              <div className="rounded-lg bg-warning-50 p-3 dark:bg-warning-900/20">
                <p className="text-xs text-warning-600 dark:text-warning-400">نسبة الفوز</p>
                <p className="text-xl font-bold text-neutral-900 dark:text-neutral-100">{Math.round(d.pipeline.win_rate * 100)}%</p>
              </div>
            </div>

            {d.pipeline.by_stage.length > 0 && (
              <div className="space-y-3 pt-2">
                <h3 className="text-sm font-medium text-neutral-700 dark:text-neutral-300">حسب المرحلة</h3>
                {d.pipeline.by_stage.map((stage) => (
                  <ProgressBar
                    key={stage.stage}
                    label={stage.stage}
                    value={stage.val}
                    max={d.pipeline.total_value}
                    color="bg-info-500"
                  />
                ))}
              </div>
            )}

            <div className="rounded-lg border border-neutral-100 bg-neutral-50 p-3 dark:border-neutral-700 dark:bg-neutral-800">
              <div className="flex items-center justify-between text-sm">
                <span className="text-neutral-600 dark:text-neutral-400">متوسط حجم الصفقة</span>
                <span className="font-bold text-neutral-900 dark:text-neutral-100">{formatNumber(d.pipeline.avg_deal_size)} ر.س</span>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Growth & Renewals */}
        <div className="space-y-6">
          {/* Growth */}
          <Card>
            <CardHeader>
              <div className="flex items-center gap-2">
                <TrendingUp className="h-5 w-5 text-success-600" />
                <h2 className="text-lg font-bold text-neutral-900 dark:text-neutral-100">النمو (آخر 30 يوم)</h2>
              </div>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 gap-4">
                <div className="flex items-center gap-3">
                  <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-info-100 dark:bg-info-900/50">
                    <Building2 className="h-5 w-5 text-info-600 dark:text-info-400" />
                  </div>
                  <div>
                    <p className="text-xs text-neutral-500 dark:text-neutral-400">شركات جديدة</p>
                    <p className="text-lg font-bold text-neutral-900 dark:text-neutral-100">{d.growth.new_companies_30d}</p>
                  </div>
                </div>
                <div className="flex items-center gap-3">
                  <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-success-100 dark:bg-success-900/50">
                    <UserPlus className="h-5 w-5 text-success-600 dark:text-success-400" />
                  </div>
                  <div>
                    <p className="text-xs text-neutral-500 dark:text-neutral-400">جهات اتصال جديدة</p>
                    <p className="text-lg font-bold text-neutral-900 dark:text-neutral-100">{d.growth.new_contacts_30d}</p>
                  </div>
                </div>
                <div className="flex items-center gap-3">
                  <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-warning-100 dark:bg-warning-900/50">
                    <Target className="h-5 w-5 text-warning-600 dark:text-warning-400" />
                  </div>
                  <div>
                    <p className="text-xs text-neutral-500 dark:text-neutral-400">فرص جديدة</p>
                    <p className="text-lg font-bold text-neutral-900 dark:text-neutral-100">{d.growth.new_opportunities_30d}</p>
                  </div>
                </div>
                <div className="flex items-center gap-3">
                  <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-purple-100 dark:bg-purple-900/50">
                    <FileSignature className="h-5 w-5 text-purple-600 dark:text-purple-400" />
                  </div>
                  <div>
                    <p className="text-xs text-neutral-500 dark:text-neutral-400">عقود جديدة</p>
                    <p className="text-lg font-bold text-neutral-900 dark:text-neutral-100">{d.growth.new_contracts_30d}</p>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Renewals */}
          <Card>
            <CardHeader>
              <div className="flex items-center gap-2">
                <Calendar className="h-5 w-5 text-orange-600" />
                <h2 className="text-lg font-bold text-neutral-900 dark:text-neutral-100">تجديد العقود</h2>
              </div>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 gap-4">
                <div className="rounded-lg bg-orange-50 p-4 text-center dark:bg-orange-900/20">
                  <p className="text-xs text-orange-600 dark:text-orange-400">خلال 30 يوم</p>
                  <p className="text-2xl font-bold text-neutral-900 dark:text-neutral-100">{d.renewals.due_next_30_days}</p>
                </div>
                <div className="rounded-lg bg-warning-50 p-4 text-center dark:bg-warning-900/20">
                  <p className="text-xs text-warning-600 dark:text-warning-400">خلال 90 يوم</p>
                  <p className="text-2xl font-bold text-neutral-900 dark:text-neutral-100">{d.renewals.due_next_90_days}</p>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>

      {/* Health Footer */}
      <Card>
        <CardContent className="p-4">
          <div className="flex flex-wrap items-center justify-between gap-4 text-sm">
            <div className="flex items-center gap-2">
              <Activity className="h-4 w-4 text-neutral-500" />
              <span className="text-neutral-600 dark:text-neutral-400">حالة المزامنة:</span>
              <Badge variant={d.health.sync_status === "synced" ? "success" : "warning"}>
                {d.health.sync_status === "synced" ? "متزامن" : "غير متزامن"}
              </Badge>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-neutral-600 dark:text-neutral-400">اكتمال البيانات:</span>
              <span className="font-medium text-neutral-900 dark:text-neutral-100">{Math.round(d.health.data_completeness * 100)}%</span>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
