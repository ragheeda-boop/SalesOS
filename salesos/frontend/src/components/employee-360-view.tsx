"use client";

import { useEmployee360 } from "@/lib/hooks/employeeQueries";
import { Card, CardContent, CardHeader, Badge, cn } from "@salesos/ui";
import { formatNumber, formatDate } from "@/lib/utils";
import { TimelineWidget } from "./timeline-widget";
import {
  User, Building2, Target, DollarSign, TrendingUp, Calendar,
  Mail, Phone, CheckSquare, MessageSquare, FileText, Award,
  Clock, AlertTriangle, Lightbulb, Star, Users, BarChart3, Activity
} from "lucide-react";

interface Employee360ViewProps {
  employeeId: string;
}

function StatBox({ icon: Icon, label, value, color }: { icon: React.ElementType; label: string; value: string | number; color: string }) {
  return (
    <div className={cn("flex items-center gap-3 rounded-lg p-3", color)}>
      <Icon className="h-5 w-5 shrink-0" />
      <div>
        <p className="text-xs">{label}</p>
        <p className="text-lg font-bold">{value}</p>
      </div>
    </div>
  );
}

export function Employee360View({ employeeId }: Employee360ViewProps) {
  const { data, isLoading } = useEmployee360(employeeId);

  if (isLoading) {
    return (
      <div className="space-y-6">
        <Card><CardContent className="p-6"><div className="h-32 animate-pulse rounded bg-neutral-200 dark:bg-neutral-700" /></CardContent></Card>
        <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
          {Array.from({ length: 3 }).map((_, i) => (
            <Card key={i}><CardContent className="p-6"><div className="h-24 animate-pulse rounded bg-neutral-200 dark:bg-neutral-700" /></CardContent></Card>
          ))}
        </div>
      </div>
    );
  }

  if (!data) {
    return <div className="py-20 text-center text-neutral-500">فشل تحميل البيانات</div>;
  }

  const d = data;
  const initials = d.profile.full_name.split(" ").map((n) => n[0]).join("").slice(0, 2).toUpperCase();

  return (
    <div className="space-y-6">
      {/* Profile Header */}
      <Card className="overflow-hidden">
        <div className="h-24 bg-gradient-to-l from-info-600 to-purple-600" />
        <CardContent className="relative px-6 pb-6 pt-0">
          <div className="flex flex-wrap items-end gap-4 -mt-12">
            <div className="flex h-20 w-20 items-center justify-center rounded-full border-4 border-white bg-info-100 text-xl font-bold text-info-700 shadow-muhide-3 dark:border-neutral-900 dark:bg-info-900 dark:text-info-300">
              {d.profile.avatar_url ? (
                <img src={d.profile.avatar_url} alt="" className="h-full w-full rounded-full object-cover" />
              ) : initials}
            </div>
            <div className="flex-1 pt-2">
              <h1 className="text-xl font-bold text-neutral-900 dark:text-neutral-100">
                {d.profile.full_name_ar || d.profile.full_name}
              </h1>
              <p className="text-sm text-neutral-500 dark:text-neutral-400">{d.profile.role} · {d.profile.email}</p>
            </div>
            <Badge variant={d.profile.is_active ? "success" : "default"}>
              {d.profile.is_active ? "نشط" : "غير نشط"}
            </Badge>
          </div>

          {d.profile.team.length > 0 && (
            <div className="mt-4 flex flex-wrap items-center gap-4 border-t border-neutral-100 pt-4 dark:border-neutral-700">
              <span className="flex items-center gap-1 text-xs text-neutral-500">
                <Users className="h-3 w-3" /> الفريق:
              </span>
              {d.profile.team.map((member: Record<string, unknown>, i: number) => (
                <span key={i} className="text-xs text-neutral-700 dark:text-neutral-300">{String(member.full_name || member.name)}</span>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* KPI Cards */}
      <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
        <StatBox icon={DollarSign} label="الإيرادات" value={`${formatNumber(d.kpis.revenue)} ر.س`} color="bg-success-50 text-success-700 dark:bg-success-900/30 dark:text-success-400" />
        <StatBox icon={Target} label="قيمة الصفقات" value={`${formatNumber(d.kpis.pipeline)} ر.س`} color="bg-info-50 text-info-700 dark:bg-info-900/30 dark:text-info-400" />
        <StatBox icon={Award} label="نسبة الفوز" value={`${Math.round(d.kpis.win_rate * 100)}%`} color="bg-purple-50 text-purple-700 dark:bg-purple-900/30 dark:text-purple-400" />
        <StatBox icon={Activity} label="الإنتاجية" value={`${Math.round(d.kpis.productivity * 100)}%`} color="bg-orange-50 text-orange-700 dark:bg-orange-900/30 dark:text-orange-400" />
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        {/* Activity Intelligence */}
        <Card>
          <CardHeader>
            <div className="flex items-center gap-2">
              <BarChart3 className="h-5 w-5 text-info-600" />
              <h2 className="text-lg font-bold text-neutral-900 dark:text-neutral-100">نشاطات</h2>
            </div>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 gap-3">
              <div className="flex items-center gap-2 rounded-lg bg-neutral-50 p-2.5 dark:bg-neutral-800">
                <Calendar className="h-4 w-4 text-purple-600" />
                <div>
                  <p className="text-xs text-neutral-500">اجتماعات</p>
                  <p className="font-bold text-neutral-900 dark:text-neutral-100">{d.activity_intelligence.meetings}</p>
                </div>
              </div>
              <div className="flex items-center gap-2 rounded-lg bg-neutral-50 p-2.5 dark:bg-neutral-800">
                <Mail className="h-4 w-4 text-info-600" />
                <div>
                  <p className="text-xs text-neutral-500">إيميلات</p>
                  <p className="font-bold text-neutral-900 dark:text-neutral-100">{d.activity_intelligence.emails}</p>
                </div>
              </div>
              <div className="flex items-center gap-2 rounded-lg bg-neutral-50 p-2.5 dark:bg-neutral-800">
                <Phone className="h-4 w-4 text-success-600" />
                <div>
                  <p className="text-xs text-neutral-500">مكالمات</p>
                  <p className="font-bold text-neutral-900 dark:text-neutral-100">{d.activity_intelligence.calls}</p>
                </div>
              </div>
              <div className="flex items-center gap-2 rounded-lg bg-neutral-50 p-2.5 dark:bg-neutral-800">
                <CheckSquare className="h-4 w-4 text-orange-600" />
                <div>
                  <p className="text-xs text-neutral-500">مهام</p>
                  <p className="font-bold text-neutral-900 dark:text-neutral-100">{d.activity_intelligence.tasks}</p>
                </div>
              </div>
              <div className="flex items-center gap-2 rounded-lg bg-neutral-50 p-2.5 dark:bg-neutral-800">
                <MessageSquare className="h-4 w-4 text-neutral-600" />
                <div>
                  <p className="text-xs text-neutral-500">ملاحظات</p>
                  <p className="font-bold text-neutral-900 dark:text-neutral-100">{d.activity_intelligence.notes}</p>
                </div>
              </div>
              <div className="flex items-center gap-2 rounded-lg bg-neutral-50 p-2.5 dark:bg-neutral-800">
                <FileText className="h-4 w-4 text-danger-600" />
                <div>
                  <p className="text-xs text-neutral-500">مستندات</p>
                  <p className="font-bold text-neutral-900 dark:text-neutral-100">{d.activity_intelligence.documents}</p>
                </div>
              </div>
            </div>
            {d.activity_intelligence.total > 0 && (
              <p className="mt-3 text-center text-xs text-neutral-500">إجمالي {d.activity_intelligence.total} نشاط</p>
            )}
          </CardContent>
        </Card>

        {/* Pipeline */}
        <Card>
          <CardHeader>
            <div className="flex items-center gap-2">
              <TrendingUp className="h-5 w-5 text-success-600" />
              <h2 className="text-lg font-bold text-neutral-900 dark:text-neutral-100">الصفقات</h2>
            </div>
          </CardHeader>
          <CardContent>
            {d.portfolio.pipeline.length === 0 ? (
              <p className="py-4 text-center text-sm text-neutral-500">لا توجد صفقات</p>
            ) : (
              <div className="space-y-3">
                {d.portfolio.pipeline.map((item, i) => (
                  <div key={i} className="flex items-center justify-between rounded-lg bg-neutral-50 p-2.5 dark:bg-neutral-800">
                    <div className="min-w-0 flex-1">
                      <p className="text-sm font-medium text-neutral-900 dark:text-neutral-100 truncate">{item.name}</p>
                      {item.company_name && (
                        <p className="text-xs text-neutral-500 truncate">{item.company_name}</p>
                      )}
                    </div>
                    <div className="text-right mr-3">
                      <p className="text-sm font-bold text-neutral-900 dark:text-neutral-100">{formatNumber(item.value)} ر.س</p>
                      <Badge variant={item.status === "won" ? "success" : item.status === "lost" ? "danger" : "primary"}>
                        {item.status}
                      </Badge>
                    </div>
                  </div>
                ))}
                <div className="flex items-center justify-between border-t border-neutral-100 pt-2 dark:border-neutral-700">
                  <span className="text-sm text-neutral-600 dark:text-neutral-400">إجمالي</span>
                  <span className="font-bold text-neutral-900 dark:text-neutral-100">{formatNumber(d.portfolio.revenue)} ر.س</span>
                </div>
              </div>
            )}
          </CardContent>
        </Card>

        {/* AI Coach */}
        <Card>
          <CardHeader>
            <div className="flex items-center gap-2">
              <Lightbulb className="h-5 w-5 text-warning-600" />
              <h2 className="text-lg font-bold text-neutral-900 dark:text-neutral-100">مدرب AI</h2>
            </div>
          </CardHeader>
          <CardContent>
            {d.ai_coach.length === 0 ? (
              <p className="py-4 text-center text-sm text-neutral-500">كل شيء على ما يرام</p>
            ) : (
              <div className="space-y-3">
                {d.ai_coach.map((action, i) => (
                  <div key={i} className={cn(
                    "rounded-lg border p-3",
                    action.priority === "high" ? "border-danger-200 bg-danger-50 dark:border-danger-900 dark:bg-danger-900/20" :
                    action.priority === "medium" ? "border-warning-200 bg-warning-50 dark:border-warning-900 dark:bg-warning-900/20" :
                    "border-info-200 bg-info-50 dark:border-info-900 dark:bg-info-900/20"
                  )}>
                    <div className="flex items-center gap-2">
                      {action.priority === "high" ? <AlertTriangle className="h-4 w-4 text-danger-600" /> :
                       action.priority === "medium" ? <Clock className="h-4 w-4 text-warning-600" /> :
                       <Star className="h-4 w-4 text-info-600" />}
                      <p className="text-sm font-medium text-neutral-900 dark:text-neutral-100">{action.title}</p>
                    </div>
                    <p className="mt-1 text-xs text-neutral-600 dark:text-neutral-400">{action.description}</p>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Calendar Intelligence */}
      {d.calendar_intelligence.today_count > 0 && (
        <Card>
          <CardHeader>
            <div className="flex items-center gap-2">
              <Calendar className="h-5 w-5 text-purple-600" />
              <h2 className="text-lg font-bold text-neutral-900 dark:text-neutral-100">التقويم</h2>
            </div>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
              <div className="text-center">
                <p className="text-2xl font-bold text-neutral-900 dark:text-neutral-100">{d.calendar_intelligence.today_count}</p>
                <p className="text-xs text-neutral-500">اليوم</p>
              </div>
              <div className="text-center">
                <p className="text-2xl font-bold text-neutral-900 dark:text-neutral-100">{d.calendar_intelligence.week_count}</p>
                <p className="text-xs text-neutral-500">هذا الأسبوع</p>
              </div>
              <div className="text-center">
                <p className="text-2xl font-bold text-neutral-900 dark:text-neutral-100">{d.calendar_intelligence.month_count}</p>
                <p className="text-xs text-neutral-500">هذا الشهر</p>
              </div>
              <div className="text-center">
                <p className="text-2xl font-bold text-neutral-900 dark:text-neutral-100">{d.calendar_intelligence.total_hours.toFixed(1)}</p>
                <p className="text-xs text-neutral-500">ساعة</p>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Timeline */}
      <TimelineWidget
        entityType="user"
        entityId={employeeId}
        title="النشاطات الأخيرة"
      />
    </div>
  );
}
