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
            <p className="text-xs font-medium text-gray-500 dark:text-gray-400">{title}</p>
            <p className="text-2xl font-bold text-gray-900 dark:text-gray-100">{value}</p>
            {subtitle && <p className="text-xs text-gray-500 dark:text-gray-400">{subtitle}</p>}
            {trend !== undefined && (
              <span className={cn("inline-flex items-center gap-0.5 text-xs", trendUp ? "text-green-600" : "text-red-600")}>
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
        <span className="text-gray-600 dark:text-gray-400">{label}</span>
        <span className="font-medium text-gray-900 dark:text-gray-100">{formatNumber(value)}</span>
      </div>
      <div className="h-2 w-full overflow-hidden rounded-full bg-gray-200 dark:bg-gray-700">
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
            <Card key={i}><CardContent className="p-5"><div className="h-20 animate-pulse rounded bg-gray-200 dark:bg-gray-700" /></CardContent></Card>
          ))}
        </div>
      </div>
    );
  }

  if (!data) {
    return (
      <div className="flex items-center justify-center py-20">
        <p className="text-gray-500 dark:text-gray-400">فشل تحميل البيانات</p>
      </div>
    );
  }

  const d = data;
  const healthColor = d.health.overall_health === "good" ? "text-green-600 bg-green-100" :
    d.health.overall_health === "warning" ? "text-yellow-600 bg-yellow-100" : "text-red-600 bg-red-100";

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">لوحة القيادة التنفيذية</h1>
          <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">نظرة شاملة على أداء المنصة والمؤشرات الرئيسية</p>
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
          color="bg-green-600"
        />
        <KPICard
          title="قيمة الصفقات"
          value={`${formatNumber(d.revenue.total_pipeline)} ر.س`}
          subtitle={`المرجح: ${formatNumber(d.revenue.weighted_pipeline)} ر.س`}
          icon={TrendingUp}
          color="bg-blue-600"
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
          color="bg-red-600"
        />
      </div>

      {/* Main Grid */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        {/* Pipeline Health */}
        <Card>
          <CardHeader>
            <div className="flex items-center gap-2">
              <BarChart3 className="h-5 w-5 text-blue-600" />
              <h2 className="text-lg font-bold text-gray-900 dark:text-gray-100">صحة الصفقات</h2>
            </div>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div className="rounded-lg bg-blue-50 p-3 dark:bg-blue-900/20">
                <p className="text-xs text-blue-600 dark:text-blue-400">إجمالي الصفقات</p>
                <p className="text-xl font-bold text-gray-900 dark:text-gray-100">{d.pipeline.total_deals}</p>
              </div>
              <div className="rounded-lg bg-green-50 p-3 dark:bg-green-900/20">
                <p className="text-xs text-green-600 dark:text-green-400">الصفقات الرابحة</p>
                <p className="text-xl font-bold text-gray-900 dark:text-gray-100">{d.pipeline.won_deals}</p>
              </div>
              <div className="rounded-lg bg-red-50 p-3 dark:bg-red-900/20">
                <p className="text-xs text-red-600 dark:text-red-400">الصفقات الخاسرة</p>
                <p className="text-xl font-bold text-gray-900 dark:text-gray-100">{d.pipeline.lost_deals}</p>
              </div>
              <div className="rounded-lg bg-yellow-50 p-3 dark:bg-yellow-900/20">
                <p className="text-xs text-yellow-600 dark:text-yellow-400">نسبة الفوز</p>
                <p className="text-xl font-bold text-gray-900 dark:text-gray-100">{Math.round(d.pipeline.win_rate * 100)}%</p>
              </div>
            </div>

            {d.pipeline.by_stage.length > 0 && (
              <div className="space-y-3 pt-2">
                <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300">حسب المرحلة</h3>
                {d.pipeline.by_stage.map((stage) => (
                  <ProgressBar
                    key={stage.stage}
                    label={stage.stage}
                    value={stage.val}
                    max={d.pipeline.total_value}
                    color="bg-blue-500"
                  />
                ))}
              </div>
            )}

            <div className="rounded-lg border border-gray-100 bg-gray-50 p-3 dark:border-gray-700 dark:bg-gray-800">
              <div className="flex items-center justify-between text-sm">
                <span className="text-gray-600 dark:text-gray-400">متوسط حجم الصفقة</span>
                <span className="font-bold text-gray-900 dark:text-gray-100">{formatNumber(d.pipeline.avg_deal_size)} ر.س</span>
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
                <TrendingUp className="h-5 w-5 text-green-600" />
                <h2 className="text-lg font-bold text-gray-900 dark:text-gray-100">النمو (آخر 30 يوم)</h2>
              </div>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 gap-4">
                <div className="flex items-center gap-3">
                  <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-blue-100 dark:bg-blue-900/50">
                    <Building2 className="h-5 w-5 text-blue-600 dark:text-blue-400" />
                  </div>
                  <div>
                    <p className="text-xs text-gray-500 dark:text-gray-400">شركات جديدة</p>
                    <p className="text-lg font-bold text-gray-900 dark:text-gray-100">{d.growth.new_companies_30d}</p>
                  </div>
                </div>
                <div className="flex items-center gap-3">
                  <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-green-100 dark:bg-green-900/50">
                    <UserPlus className="h-5 w-5 text-green-600 dark:text-green-400" />
                  </div>
                  <div>
                    <p className="text-xs text-gray-500 dark:text-gray-400">جهات اتصال جديدة</p>
                    <p className="text-lg font-bold text-gray-900 dark:text-gray-100">{d.growth.new_contacts_30d}</p>
                  </div>
                </div>
                <div className="flex items-center gap-3">
                  <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-yellow-100 dark:bg-yellow-900/50">
                    <Target className="h-5 w-5 text-yellow-600 dark:text-yellow-400" />
                  </div>
                  <div>
                    <p className="text-xs text-gray-500 dark:text-gray-400">فرص جديدة</p>
                    <p className="text-lg font-bold text-gray-900 dark:text-gray-100">{d.growth.new_opportunities_30d}</p>
                  </div>
                </div>
                <div className="flex items-center gap-3">
                  <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-purple-100 dark:bg-purple-900/50">
                    <FileSignature className="h-5 w-5 text-purple-600 dark:text-purple-400" />
                  </div>
                  <div>
                    <p className="text-xs text-gray-500 dark:text-gray-400">عقود جديدة</p>
                    <p className="text-lg font-bold text-gray-900 dark:text-gray-100">{d.growth.new_contracts_30d}</p>
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
                <h2 className="text-lg font-bold text-gray-900 dark:text-gray-100">تجديد العقود</h2>
              </div>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 gap-4">
                <div className="rounded-lg bg-orange-50 p-4 text-center dark:bg-orange-900/20">
                  <p className="text-xs text-orange-600 dark:text-orange-400">خلال 30 يوم</p>
                  <p className="text-2xl font-bold text-gray-900 dark:text-gray-100">{d.renewals.due_next_30_days}</p>
                </div>
                <div className="rounded-lg bg-yellow-50 p-4 text-center dark:bg-yellow-900/20">
                  <p className="text-xs text-yellow-600 dark:text-yellow-400">خلال 90 يوم</p>
                  <p className="text-2xl font-bold text-gray-900 dark:text-gray-100">{d.renewals.due_next_90_days}</p>
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
              <Activity className="h-4 w-4 text-gray-500" />
              <span className="text-gray-600 dark:text-gray-400">حالة المزامنة:</span>
              <Badge variant={d.health.sync_status === "synced" ? "success" : "warning"}>
                {d.health.sync_status === "synced" ? "متزامن" : "غير متزامن"}
              </Badge>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-gray-600 dark:text-gray-400">اكتمال البيانات:</span>
              <span className="font-medium text-gray-900 dark:text-gray-100">{Math.round(d.health.data_completeness * 100)}%</span>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
