"use client";

import { useState } from "react";
import { useEmployee360 } from "@/lib/hooks/employeeQueries";
import { Avatar, Card, CardContent, CardHeader, Badge, cn, Tabs, TabsList, Tab, TabsPanel } from "@salesos/ui";
import { formatNumber } from "@/lib/utils";
import { TimelineWidget } from "./timeline-widget";
import {
  User, Building2, Target, DollarSign, TrendingUp, Calendar,
  Mail, Phone, CheckSquare, MessageSquare, FileText, Award,
  Clock, AlertTriangle, Lightbulb, Star, Users, BarChart3, Activity,
  Send, Reply, Timer, Briefcase, Handshake, Sparkles, ArrowUpRight,
  ExternalLink, Link2, Globe,
} from "lucide-react";

interface Employee360ViewProps {
  employeeId: string;
}

type TabId = "overview" | "activity" | "pipeline" | "ai" | "timeline";

const TABS: { id: TabId; label: string; icon: typeof Activity }[] = [
  { id: "overview", label: "نظرة عامة", icon: User },
  { id: "activity", label: "النشاطات", icon: BarChart3 },
  { id: "pipeline", label: "الصفقات", icon: TrendingUp },
  { id: "ai", label: "AI Coach", icon: Sparkles },
  { id: "timeline", label: "الجدول الزمني", icon: Clock },
];

function StatBox({ icon: Icon, label, value, color, trend }: { icon: React.ElementType; label: string; value: string | number; color: string; trend?: "up" | "stable" | "down" }) {
  const trendIcon = trend === "up" ? "↑" : trend === "down" ? "↓" : "→";
  const trendColor = trend === "up" ? "text-success-600" : trend === "down" ? "text-danger-600" : "text-neutral-400";
  return (
    <div className={cn("flex items-center gap-3 rounded-xl p-3", color)}>
      <Icon className="h-5 w-5 shrink-0" />
      <div>
        <p className="text-[10px] opacity-70">{label}</p>
        <p className="text-lg font-bold">
          {value}
          {trend && <span className={cn("ms-1 text-xs", trendColor)}>{trendIcon}</span>}
        </p>
      </div>
    </div>
  );
}

function MetricBar({ label, value, max = 100, color }: { label: string; value: number; max?: number; color?: string }) {
  const pct = Math.min(100, (value / max) * 100);
  const bar = color ?? (pct >= 70 ? "bg-success-500" : pct >= 40 ? "bg-warning-500" : "bg-danger-500");
  return (
    <div>
      <div className="flex items-center justify-between text-[10px] text-neutral-500 dark:text-neutral-400">
        <span>{label}</span>
        <span className="font-semibold text-neutral-900 dark:text-neutral-100">{Math.round(pct)}%</span>
      </div>
      <div className="mt-1 h-1.5 w-full overflow-hidden rounded-full bg-neutral-100 dark:bg-neutral-800">
        <div className={cn("h-full rounded-full transition-all", bar)} style={{ width: `${pct}%` }} />
      </div>
    </div>
  );
}

export function Employee360View({ employeeId }: Employee360ViewProps) {
  const { data, isLoading } = useEmployee360(employeeId);
  const [activeTab, setActiveTab] = useState<TabId>("overview");

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div className="h-32 animate-pulse rounded-xl bg-neutral-100 dark:bg-neutral-800" />
        <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
          {Array.from({ length: 4 }).map((_, i) => (
            <div key={i} className="h-20 animate-pulse rounded-xl bg-neutral-100 dark:bg-neutral-800" />
          ))}
        </div>
        <div className="h-64 animate-pulse rounded-xl bg-neutral-100 dark:bg-neutral-800" />
      </div>
    );
  }

  if (!data) {
    return (
      <div className="flex flex-col items-center justify-center py-20 text-center">
        <AlertTriangle className="mb-3 h-10 w-10 text-danger-500" />
        <p className="text-lg font-semibold text-neutral-900 dark:text-neutral-100">فشل تحميل البيانات</p>
        <p className="mt-1 text-sm text-neutral-500">تأكد من اتصال الخادم وحاول مرة أخرى</p>
      </div>
    );
  }

  const d = data;
  const initials = d.profile.full_name.split(" ").map((n) => n[0]).join("").slice(0, 2).toUpperCase();

  return (
    <div className="space-y-4">
      {/* Profile Header */}
      <div className="overflow-hidden rounded-xl border border-neutral-200 bg-white shadow-muhide-1 dark:border-neutral-700 dark:bg-neutral-900">
        <div className="h-20 bg-gradient-to-l from-info-600 via-purple-600 to-[var(--muhide-orange)]" />
        <div className="relative px-6 pb-5 pt-0">
          <div className="flex flex-wrap items-end gap-4 -mt-10">
            <Avatar
              src={d.profile.avatar_url || undefined}
              alt={d.profile.full_name}
              fallback={initials}
              size="lg"
              className="h-20 w-20 text-xl border-4 border-white shadow-muhide-3 dark:border-neutral-900"
            />
            <div className="flex-1 pt-2">
              <h1 className="text-xl font-bold text-neutral-900 dark:text-neutral-100">
                {d.profile.full_name_ar || d.profile.full_name}
              </h1>
              <p className="text-sm text-neutral-500 dark:text-neutral-400">
                {d.profile.role}
                {d.profile.email && <span className="ms-2">· {d.profile.email}</span>}
              </p>
            </div>
            <div className="flex items-center gap-2">
              <Badge variant={d.profile.is_active ? "success" : "default"}>
                {d.profile.is_active ? "نشط" : "غير نشط"}
              </Badge>
              {d.profile.phone && (
                <a href={`tel:${d.profile.phone}`} className="inline-flex items-center gap-1 rounded-lg border border-neutral-200 px-2 py-1 text-xs text-neutral-600 hover:bg-neutral-50 dark:border-neutral-700 dark:text-neutral-400 dark:hover:bg-neutral-800">
                  <Phone className="h-3 w-3" /> اتصال
                </a>
              )}
              {d.profile.email && (
                <a href={`mailto:${d.profile.email}`} className="inline-flex items-center gap-1 rounded-lg border border-neutral-200 px-2 py-1 text-xs text-neutral-600 hover:bg-neutral-50 dark:border-neutral-700 dark:text-neutral-400 dark:hover:bg-neutral-800">
                  <Mail className="h-3 w-3" /> بريد
                </a>
              )}
            </div>
          </div>

          {/* Manager + Team */}
          <div className="mt-4 flex flex-wrap items-center gap-4 border-t border-neutral-100 pt-4 dark:border-neutral-700">
            {d.profile.manager && (
              <div className="flex items-center gap-2 text-sm">
                <span className="text-neutral-500">المدير:</span>
                <span className="font-medium text-neutral-900 dark:text-neutral-100">
                  {String(d.profile.manager.full_name || d.profile.manager.name || "غير محدد")}
                </span>
              </div>
            )}
            {d.profile.team.length > 0 && (
              <div className="flex items-center gap-2">
                <Users className="h-3.5 w-3.5 text-neutral-400" />
                <span className="text-xs text-neutral-500">الفريق ({d.profile.team.length}):</span>
                <div className="flex -space-x-2">
                  {d.profile.team.slice(0, 5).map((member: Record<string, unknown>, i: number) => (
                    <span
                      key={i}
                      title={String(member.full_name || member.name)}
                    >
                      <Avatar
                        size="sm"
                        fallback={String(member.full_name || member.name || "").split(" ").map((n: string) => n[0]).join("").slice(0, 2).toUpperCase()}
                        className="h-6 w-6 border-2 border-white text-[8px] dark:border-neutral-900"
                      />
                    </span>
                  ))}
                  {d.profile.team.length > 5 && (
                    <div className="flex h-6 w-6 items-center justify-center rounded-full border-2 border-white bg-neutral-200 text-[8px] font-bold text-neutral-600 dark:border-neutral-900 dark:bg-neutral-700 dark:text-neutral-300">
                      +{d.profile.team.length - 5}
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
        <StatBox icon={DollarSign} label="الإيرادات" value={`${formatNumber(d.kpis.revenue)} ر.س`} color="bg-success-50 text-success-700 dark:bg-success-900/20 dark:text-success-400" trend="up" />
        <StatBox icon={Target} label="قيمة الصفقات" value={`${formatNumber(d.kpis.pipeline)} ر.س`} color="bg-info-50 text-info-700 dark:bg-info-900/20 dark:text-info-400" />
        <StatBox icon={Award} label="نسبة الفوز" value={`${Math.round(d.kpis.win_rate * 100)}%`} color="bg-purple-50 text-purple-700 dark:bg-purple-900/20 dark:text-purple-400" />
        <StatBox icon={Activity} label="الإنتاجية" value={`${Math.round(d.kpis.productivity * 100)}%`} color="bg-warning-50 text-warning-700 dark:bg-warning-900/20 dark:text-warning-400" />
      </div>

      <Tabs value={activeTab} onValueChange={(v) => setActiveTab(v as TabId)}>
        <TabsList className="flex items-center gap-1 overflow-x-auto rounded-xl border border-neutral-200 bg-white px-2 py-1 dark:border-neutral-700 dark:bg-neutral-900">
          {TABS.map((tab) => {
            const Icon = tab.icon;
            return (
              <Tab
                key={tab.id}
                value={tab.id}
                className="flex items-center gap-1.5 whitespace-nowrap rounded-lg border-b-0 px-3 py-2 data-[state=active]:bg-[var(--muhide-orange)]/10 data-[state=active]:text-[var(--muhide-orange)] data-[state=active]:border-b-0 dark:data-[state=active]:bg-[var(--muhide-orange)]/20 dark:data-[state=active]:text-orange-300"
              >
                <Icon className="h-4 w-4" />
                <span className="hidden sm:inline">{tab.label}</span>
              </Tab>
            );
          })}
        </TabsList>

        <TabsPanel value="overview">
          <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
            {/* Activity Intelligence */}
            <Card>
              <CardHeader>
                <div className="flex items-center gap-2">
                  <BarChart3 className="h-5 w-5 text-info-600" />
                  <h2 className="text-lg font-bold text-neutral-900 dark:text-neutral-100">النشاطات</h2>
                </div>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-2 gap-2">
                  <div className="flex items-center gap-2 rounded-lg bg-neutral-50 p-2.5 dark:bg-neutral-800">
                    <Calendar className="h-4 w-4 text-purple-600" />
                    <div>
                      <p className="text-[10px] text-neutral-500">اجتماعات</p>
                      <p className="font-bold text-neutral-900 dark:text-neutral-100">{d.activity_intelligence.meetings}</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-2 rounded-lg bg-neutral-50 p-2.5 dark:bg-neutral-800">
                    <Mail className="h-4 w-4 text-info-600" />
                    <div>
                      <p className="text-[10px] text-neutral-500">إيميلات</p>
                      <p className="font-bold text-neutral-900 dark:text-neutral-100">{d.activity_intelligence.emails}</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-2 rounded-lg bg-neutral-50 p-2.5 dark:bg-neutral-800">
                    <Phone className="h-4 w-4 text-success-600" />
                    <div>
                      <p className="text-[10px] text-neutral-500">مكالمات</p>
                      <p className="font-bold text-neutral-900 dark:text-neutral-100">{d.activity_intelligence.calls}</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-2 rounded-lg bg-neutral-50 p-2.5 dark:bg-neutral-800">
                    <CheckSquare className="h-4 w-4 text-warning-600" />
                    <div>
                      <p className="text-[10px] text-neutral-500">مهام</p>
                      <p className="font-bold text-neutral-900 dark:text-neutral-100">{d.activity_intelligence.tasks}</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-2 rounded-lg bg-neutral-50 p-2.5 dark:bg-neutral-800">
                    <MessageSquare className="h-4 w-4 text-neutral-600" />
                    <div>
                      <p className="text-[10px] text-neutral-500">ملاحظات</p>
                      <p className="font-bold text-neutral-900 dark:text-neutral-100">{d.activity_intelligence.notes}</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-2 rounded-lg bg-neutral-50 p-2.5 dark:bg-neutral-800">
                    <FileText className="h-4 w-4 text-danger-600" />
                    <div>
                      <p className="text-[10px] text-neutral-500">مستندات</p>
                      <p className="font-bold text-neutral-900 dark:text-neutral-100">{d.activity_intelligence.documents}</p>
                    </div>
                  </div>
                </div>
                {d.activity_intelligence.total > 0 && (
                  <p className="mt-3 text-center text-xs text-neutral-500">إجمالي {d.activity_intelligence.total} نشاط</p>
                )}
              </CardContent>
            </Card>

            {/* Email Intelligence */}
            <Card>
              <CardHeader>
                <div className="flex items-center gap-2">
                  <Mail className="h-5 w-5 text-info-600" />
                  <h2 className="text-lg font-bold text-neutral-900 dark:text-neutral-100">البريد الإلكتروني</h2>
                </div>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  <div className="grid grid-cols-3 gap-2 text-center">
                    <div className="rounded-lg bg-neutral-50 p-2 dark:bg-neutral-800">
                      <Send className="mx-auto mb-1 h-4 w-4 text-info-600" />
                      <p className="text-lg font-bold text-neutral-900 dark:text-neutral-100">{d.email_intelligence.sent}</p>
                      <p className="text-[10px] text-neutral-500">مرسل</p>
                    </div>
                    <div className="rounded-lg bg-neutral-50 p-2 dark:bg-neutral-800">
                      <Mail className="mx-auto mb-1 h-4 w-4 text-success-600" />
                      <p className="text-lg font-bold text-neutral-900 dark:text-neutral-100">{d.email_intelligence.received}</p>
                      <p className="text-[10px] text-neutral-500">مستلم</p>
                    </div>
                    <div className="rounded-lg bg-neutral-50 p-2 dark:bg-neutral-800">
                      <Reply className="mx-auto mb-1 h-4 w-4 text-purple-600" />
                      <p className="text-lg font-bold text-neutral-900 dark:text-neutral-100">{d.email_intelligence.replies}</p>
                      <p className="text-[10px] text-neutral-500">ردود</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-2 rounded-lg bg-neutral-50 p-2 dark:bg-neutral-800">
                    <Timer className="h-4 w-4 text-warning-600" />
                    <div>
                      <p className="text-[10px] text-neutral-500">متوسط وقت الرد</p>
                      <p className="text-sm font-bold text-neutral-900 dark:text-neutral-100">{d.email_intelligence.avg_response_hours.toFixed(1)} ساعة</p>
                    </div>
                  </div>
                  {d.email_intelligence.top_companies.length > 0 && (
                    <div>
                      <p className="mb-1 text-[10px] font-medium text-neutral-500">أكثر الشركات تواصلًا</p>
                      <div className="space-y-1">
                        {d.email_intelligence.top_companies.slice(0, 3).map((c: Record<string, unknown>, i: number) => (
                          <div key={i} className="flex items-center justify-between text-xs">
                            <span className="text-neutral-700 dark:text-neutral-300">{String(c.name || c.company_name)}</span>
                            <span className="text-neutral-500">{String(c.count || c.email_count)} إيميل</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>

            {/* Calendar Intelligence */}
            <Card>
              <CardHeader>
                <div className="flex items-center gap-2">
                  <Calendar className="h-5 w-5 text-purple-600" />
                  <h2 className="text-lg font-bold text-neutral-900 dark:text-neutral-100">التقويم</h2>
                </div>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  <div className="grid grid-cols-2 gap-2">
                    <div className="rounded-lg bg-neutral-50 p-2.5 text-center dark:bg-neutral-800">
                      <p className="text-xl font-bold text-neutral-900 dark:text-neutral-100">{d.calendar_intelligence.today_count}</p>
                      <p className="text-[10px] text-neutral-500">اجتماعات اليوم</p>
                    </div>
                    <div className="rounded-lg bg-neutral-50 p-2.5 text-center dark:bg-neutral-800">
                      <p className="text-xl font-bold text-neutral-900 dark:text-neutral-100">{d.calendar_intelligence.week_count}</p>
                      <p className="text-[10px] text-neutral-500">هذا الأسبوع</p>
                    </div>
                  </div>
                  <div className="grid grid-cols-2 gap-2">
                    <div className="rounded-lg bg-neutral-50 p-2.5 text-center dark:bg-neutral-800">
                      <p className="text-xl font-bold text-neutral-900 dark:text-neutral-100">{d.calendar_intelligence.total_hours.toFixed(1)}</p>
                      <p className="text-[10px] text-neutral-500">ساعة إجمالي</p>
                    </div>
                    <div className="rounded-lg bg-neutral-50 p-2.5 text-center dark:bg-neutral-800">
                      <p className="text-xl font-bold text-neutral-900 dark:text-neutral-100">{d.calendar_intelligence.unique_companies_met}</p>
                      <p className="text-[10px] text-neutral-500">شركات تم التواصل معها</p>
                    </div>
                  </div>
                  {d.calendar_intelligence.upcoming.length > 0 && (
                    <div>
                      <p className="mb-1 text-[10px] font-medium text-neutral-500">الاجتماعات القادمة</p>
                      <div className="space-y-1">
                        {d.calendar_intelligence.upcoming.slice(0, 3).map((m: Record<string, unknown>, i: number) => (
                          <div key={i} className="flex items-center gap-2 rounded-lg bg-neutral-50 px-2 py-1.5 dark:bg-neutral-800">
                            <Calendar className="h-3 w-3 text-purple-500" />
                            <span className="text-xs text-neutral-700 dark:text-neutral-300">{String(m.title || m.subject)}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsPanel>

        <TabsPanel value="activity">
          <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
            {/* Performance Metrics */}
            <Card>
              <CardHeader>
                <div className="flex items-center gap-2">
                  <Target className="h-5 w-5 text-success-600" />
                  <h2 className="text-lg font-bold text-neutral-900 dark:text-neutral-100">أداء المبيعات</h2>
                </div>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  <MetricBar label="نسبة الاستجابة" value={d.kpis.response_rate * 100} color="bg-info-500" />
                  <MetricBar label="نسبة المتابعة" value={d.kpis.follow_up_rate * 100} color="bg-purple-500" />
                  <MetricBar label="نسبة الفوز" value={d.kpis.win_rate * 100} color="bg-success-500" />
                  <MetricBar label="الإنتاجية" value={d.kpis.productivity * 100} color="bg-warning-500" />
                </div>
                <div className="mt-4 grid grid-cols-2 gap-2">
                  <div className="rounded-lg bg-neutral-50 p-2.5 dark:bg-neutral-800">
                    <p className="text-[10px] text-neutral-500">التوقعات</p>
                    <p className="text-sm font-bold text-neutral-900 dark:text-neutral-100">{formatNumber(d.kpis.forecast)} ر.س</p>
                  </div>
                  <div className="rounded-lg bg-neutral-50 p-2.5 dark:bg-neutral-800">
                    <p className="text-[10px] text-neutral-500">النشاطات</p>
                    <p className="text-sm font-bold text-neutral-900 dark:text-neutral-100">{d.kpis.activities}</p>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Portfolio */}
            <Card>
              <CardHeader>
                <div className="flex items-center gap-2">
                  <Briefcase className="h-5 w-5 text-info-600" />
                  <h2 className="text-lg font-bold text-neutral-900 dark:text-neutral-100">المحفظة</h2>
                </div>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  <div className="grid grid-cols-2 gap-2">
                    <div className="rounded-lg bg-neutral-50 p-2.5 dark:bg-neutral-800">
                      <p className="text-[10px] text-neutral-500">الشركات</p>
                      <p className="text-lg font-bold text-neutral-900 dark:text-neutral-100">{d.portfolio.companies.length}</p>
                    </div>
                    <div className="rounded-lg bg-neutral-50 p-2.5 dark:bg-neutral-800">
                      <p className="text-[10px] text-neutral-500">الجهات</p>
                      <p className="text-lg font-bold text-neutral-900 dark:text-neutral-100">{d.portfolio.contacts.length}</p>
                    </div>
                  </div>
                  <div className="rounded-lg bg-neutral-50 p-2.5 dark:bg-neutral-800">
                    <p className="text-[10px] text-neutral-500">إجمالي الإيرادات</p>
                    <p className="text-lg font-bold text-success-600">{formatNumber(d.portfolio.revenue)} ر.س</p>
                  </div>
                  {d.portfolio.contracts.length > 0 && (
                    <div>
                      <p className="mb-1 text-[10px] font-medium text-neutral-500">العقود ({d.portfolio.contracts.length})</p>
                      <div className="space-y-1">
                        {d.portfolio.contracts.slice(0, 3).map((c, i) => (
                          <div key={i} className="flex items-center justify-between rounded-lg bg-neutral-50 px-2 py-1.5 dark:bg-neutral-800">
                            <span className="text-xs text-neutral-700 dark:text-neutral-300">{c.name}</span>
                            <span className="text-xs font-medium text-neutral-900 dark:text-neutral-100">{formatNumber(c.value)} ر.س</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsPanel>

        <TabsPanel value="pipeline">
          <Card>
            <CardHeader>
              <div className="flex items-center gap-2">
                <TrendingUp className="h-5 w-5 text-success-600" />
                <h2 className="text-lg font-bold text-neutral-900 dark:text-neutral-100">الصفقات</h2>
              </div>
            </CardHeader>
            <CardContent>
              {d.portfolio.pipeline.length === 0 ? (
                <div className="py-8 text-center text-sm text-neutral-500 dark:text-neutral-400">
                  <TrendingUp className="mx-auto mb-2 h-8 w-8 opacity-30" />
                  لا توجد صفقات حالية
                </div>
              ) : (
                <div className="space-y-2">
                  {d.portfolio.pipeline.map((item, i) => (
                    <div key={i} className="flex items-center justify-between rounded-lg border border-neutral-100 p-3 transition hover:bg-neutral-50 dark:border-neutral-800 dark:hover:bg-neutral-800/50">
                      <div className="min-w-0 flex-1">
                        <p className="text-sm font-medium text-neutral-900 dark:text-neutral-100">{item.name}</p>
                        {item.company_name && (
                          <p className="text-xs text-neutral-500">{item.company_name}</p>
                        )}
                      </div>
                      <div className="ms-4 flex items-center gap-3">
                        <span className="text-sm font-bold text-neutral-900 dark:text-neutral-100">{formatNumber(item.value)} ر.س</span>
                        <Badge variant={
                          item.status === "won" ? "success" :
                          item.status === "lost" ? "danger" :
                          item.status === "active" ? "primary" : "default"
                        }>
                          {item.status}
                        </Badge>
                      </div>
                    </div>
                  ))}
                  <div className="flex items-center justify-between border-t border-neutral-100 pt-3 dark:border-neutral-800">
                    <span className="text-sm text-neutral-600 dark:text-neutral-400">إجمالي المحفظة</span>
                    <span className="font-bold text-neutral-900 dark:text-neutral-100">{formatNumber(d.portfolio.revenue)} ر.س</span>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsPanel>

        <TabsPanel value="ai">
          <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
            {/* AI Coach */}
            <Card>
              <CardHeader>
                <div className="flex items-center gap-2">
                  <Sparkles className="h-5 w-5 text-purple-600" />
                  <h2 className="text-lg font-bold text-neutral-900 dark:text-neutral-100">مدرب AI</h2>
                </div>
              </CardHeader>
              <CardContent>
                {d.ai_coach.length === 0 ? (
                  <div className="py-8 text-center text-sm text-neutral-500 dark:text-neutral-400">
                    <Sparkles className="mx-auto mb-2 h-8 w-8 opacity-30" />
                    كل شيء على ما يرام — لا توجد توصيات
                  </div>
                ) : (
                  <div className="space-y-2">
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

            {/* Suggested Outreach */}
            <Card>
              <CardHeader>
                <div className="flex items-center gap-2">
                  <Send className="h-5 w-5 text-info-600" />
                  <h2 className="text-lg font-bold text-neutral-900 dark:text-neutral-100">اقتراحات التواصل</h2>
                </div>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {d.email_intelligence.top_contacts.length > 0 && (
                    <div>
                      <p className="mb-2 text-[10px] font-medium text-neutral-500">أكثر جهات الاتصال تفاعلًا</p>
                      <div className="space-y-1">
                        {d.email_intelligence.top_contacts.slice(0, 5).map((c: Record<string, unknown>, i: number) => (
                          <div key={i} className="flex items-center gap-2 rounded-lg bg-neutral-50 px-2.5 py-2 dark:bg-neutral-800">
                            <Avatar
                              size="sm"
                              fallback={String(c.name || "").split(" ").map((n: string) => n[0]).join("").slice(0, 2).toUpperCase()}
                              className="h-6 w-6 text-[8px]"
                            />
                            <div className="flex-1 min-w-0">
                              <p className="text-xs font-medium text-neutral-900 dark:text-neutral-100">{String(c.name)}</p>
                              {c.company ? <p className="text-[10px] text-neutral-500">{String(c.company)}</p> : null}
                            </div>
                            <span className="text-[10px] text-neutral-500">{String(c.count || c.email_count)} تواصل</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                  <div className="rounded-lg border border-dashed border-neutral-200 p-3 text-center dark:border-neutral-700">
                    <Send className="mx-auto mb-1 h-5 w-5 text-neutral-400" />
                    <p className="text-xs text-neutral-500">اقتراحات AI للتواصل ستظهر هنا</p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsPanel>

        <TabsPanel value="timeline">
          <TimelineWidget
            entityType="user"
            entityId={employeeId}
            title="النشاطات الأخيرة"
          />
        </TabsPanel>
      </Tabs>
    </div>
  );
}
