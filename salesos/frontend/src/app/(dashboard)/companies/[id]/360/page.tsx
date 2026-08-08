"use client";
/* eslint-disable custom-rules/no-tailwind-color-classes */

import { useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { useCompany } from "@/lib/hooks/companyQueries";
import { useCompany360 } from "@/lib/hooks/company360Queries";
import {
  Tabs,
  TabsList,
  Tab,
  TabsPanel,
  Breadcrumbs,
  Skeleton,
  EmptyState,
  DataTable,
  Card,
  CardContent,
  CardHeader,
  cn,
} from "@salesos/ui";
import {
  BarChart3,
  Users,
  Handshake,
  Activity,
  MoreHorizontal,
  Building2,
  MapPin,
  FileText,
  TrendingUp,
  CheckCircle,
  Plus,
  Mail,
  Phone,
  Calendar,
  MessageSquare,
  DollarSign,
  Target,
  Settings,
  Bell,
  Share2,
} from "lucide-react";
import { useTranslation } from "@/lib/i18n";
import { KnowledgeGraphPanel } from "@/features/company-intelligence/widgets/company-360/KnowledgeGraphPanel";
import { ActivityTimeline } from "@/features/company-intelligence/widgets/company-360/ActivityTimeline";
import { DecisionPlatformPanel } from "@/features/company-intelligence/widgets/company-360/DecisionPlatformPanel";
import { ErrorBoundary } from "@/components/error-boundary";
import { asArray } from "@/lib/asArray";
import type { ColumnDef } from "@tanstack/react-table";

type TabId = "overview" | "people" | "dealroom" | "activity" | "more";

const TABS: { id: TabId; labelKey: string; icon: typeof BarChart3 }[] = [
  { id: "overview", labelKey: "tabs.overview", icon: BarChart3 },
  { id: "people", labelKey: "tabs.people", icon: Users },
  { id: "dealroom", labelKey: "tabs.dealroom", icon: Handshake },
  { id: "activity", labelKey: "tabs.activity", icon: Activity },
  { id: "more", labelKey: "tabs.more", icon: MoreHorizontal },
];

interface QuickAction {
  id: string;
  label: string;
  icon: typeof Mail;
  color: string;
  href?: string;
  onClick?: string;
}

const QUICK_ACTIONS: QuickAction[] = [
  {
    id: "add-contact",
    label: "جهة اتصال",
    icon: Users,
    color: "text-[var(--color-info)] bg-[var(--color-info-bg)]",
    href: "?action=add-contact",
  },
  {
    id: "new-deal",
    label: "صفقة",
    icon: Handshake,
    color: "text-[var(--color-success)] bg-[var(--color-success-bg)]",
    href: "?action=new-deal",
  },
  {
    id: "add-note",
    label: "ملاحظة",
    icon: MessageSquare,
    color: "text-[var(--color-neutral)] bg-[var(--color-neutral-bg)]",
    href: "?action=add-note",
  },
  {
    id: "schedule-meeting",
    label: "اجتماع",
    icon: Calendar,
    color: "text-[var(--color-warning)] bg-[var(--color-warning-bg)]",
    href: "?action=schedule-meeting",
  },
  {
    id: "send-email",
    label: "بريد",
    icon: Mail,
    color: "text-[var(--color-info)] bg-[var(--color-info-bg)]",
    href: "?action=send-email",
  },
  {
    id: "log-call",
    label: "مكالمة",
    icon: Phone,
    color: "text-[var(--color-success)] bg-[var(--color-success-bg)]",
    href: "?action=log-call",
  },
];

function HealthScoreRing({ score }: { score: number }) {
  const radius = 36;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (score / 100) * circumference;
  const color = score >= 70 ? "#22c55e" : score >= 40 ? "#f59e0b" : "#ef4444";

  return (
    <div className="relative flex items-center justify-center">
      <svg width="84" height="84" viewBox="0 0 84 84">
        <circle
          cx="42"
          cy="42"
          r={radius}
          fill="none"
          stroke="currentColor"
          className="text-[var(--text-primary)]"
          strokeWidth="6"
        />
        <circle
          cx="42"
          cy="42"
          r={radius}
          fill="none"
          stroke={color}
          strokeWidth="6"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          strokeLinecap="round"
          transform="rotate(-90 42 42)"
          className="transition-all duration-700"
        />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span className="text-2xl font-bold text-[var(--text-primary)]">{score}</span>
        <span className="text-[9px] text-[var(--text-muted)]">صحة</span>
      </div>
    </div>
  );
}

function MetricBox({
  label,
  value,
  icon: Icon,
  color,
}: {
  label: string;
  value: string | number;
  icon: typeof BarChart3;
  color: string;
}) {
  return (
    <div className={cn("flex items-center gap-3 rounded-xl p-3", color)}>
      <Icon className="h-5 w-5 shrink-0" />
      <div>
        <p className="text-[10px] opacity-70">{label}</p>
        <p className="text-sm font-bold">{value}</p>
      </div>
    </div>
  );
}

function OverviewSkeleton() {
  return (
    <div className="space-y-4">
      <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
        {Array.from({ length: 4 }).map((_, i) => (
          <Skeleton key={i} variant="card" />
        ))}
      </div>
      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <Skeleton variant="card" />
        <Skeleton variant="card" />
      </div>
    </div>
  );
}

export default function Company360Page() {
  const params = useParams();
  const router = useRouter();
  const id = params.id as string;
  const { t } = useTranslation();

  const { data: company, isLoading: companyLoading, isError: companyError } = useCompany(id);
  const { data: company360, isLoading: loading360, isError: error360 } = useCompany360(id);

  const [activeTab, setActiveTab] = useState<TabId>("overview");
  const [showSampleData, setShowSampleData] = useState(false);

  const isLoading = companyLoading || loading360;
  const isError = companyError || error360;

  const breadcrumbItems = [
    { label: t("nav.companies"), href: "/companies" },
    {
      label: company?.name_ar || company?.name_en || "...",
      href: `/companies/${id}`,
    },
    { label: "360", href: undefined },
  ];

  if (isLoading) {
    return (
      <div className="space-y-4">
        <Skeleton className="h-5 w-48" />
        <Skeleton className="h-32" />
        <div className="h-10 rounded-lg bg-[var(--bg-tertiary)]" />
        <OverviewSkeleton />
      </div>
    );
  }

  if (isError || !company) {
    return (
      <div className="py-20">
        <Breadcrumbs items={breadcrumbItems} className="mb-6" />
        <EmptyState
          icon={<Building2 className="h-12 w-12" />}
          title={t("company.load_error")}
          description={t("company.load_error_hint")}
          action={{
            label: t("companies.back_to_list"),
            onClick: () => router.push("/companies"),
          }}
        />
      </div>
    );
  }

  const healthScore = company360?.health_score || company.confidence_score || 0;
  const overview = company360?.overview;
  const organization = company360?.organization;
  const enrichment = company360?.enrichment;
  const opportunities = asArray<Record<string, unknown>>(company360?.opportunities);
  const contracts = asArray<Record<string, unknown>>(company360?.contracts);
  const invoices = asArray<Record<string, unknown>>(company360?.invoices);

  const enrichmentData = [
    {
      label: "إجمالي الإيرادات",
      value: overview?.total_revenue ? `$${(overview.total_revenue / 1000).toFixed(0)}K` : "-",
    },
    { label: "العقود النشطة", value: overview?.active_contracts ?? "-" },
    { label: "جهات الاتصال", value: overview?.total_contacts ?? "-" },
    { label: "الفرص", value: overview?.total_opportunities ?? "-" },
    { label: "المهام المعلقة", value: overview?.pending_tasks ?? "-" },
    { label: "الاجتماعات القادمة", value: overview?.upcoming_meetings ?? "-" },
    { label: "مصادر البيانات", value: enrichment?.sources?.join(",") || "-" },
    {
      label: "آخر تحديث",
      value: enrichment?.last_enriched_at
        ? new Date(enrichment.last_enriched_at).toLocaleDateString("ar-SA")
        : "-",
    },
  ];

  const hierarchySections = organization
    ? [
        {
          title: "الفروع",
          icon: Building2,
          items:
            asArray<{ id: string; name: string; city: string | null; region: string | null }>(
              organization.branches
            ).map((b) => ({
              id: b.id,
              label: b.name,
              subtitle: [b.city, b.region].filter(Boolean).join(","),
            })),
        },
        {
          title: "الأقسام",
          icon: Users,
          items: asArray<string>(organization.departments).map((d, i) => ({
            id: String(i),
            label: typeof d === "string" ? d : String((d as { name?: string })?.name ?? i),
          })),
        },
      ]
    : [];

  const financialColumns: ColumnDef<Record<string, unknown>>[] = [
    {
      accessorKey: "source",
      header: "المصدر",
      cell: ({ getValue }) => String(getValue() || "-"),
    },
    {
      accessorKey: "type",
      header: "النوع",
      cell: ({ getValue }) => String(getValue() || "-"),
    },
    {
      accessorKey: "value",
      header: "القيمة",
      cell: ({ getValue }) => {
        const v = getValue();
        return typeof v === "number" ? `$${v.toLocaleString()}` : String(v || "-");
      },
    },
    {
      accessorKey: "status",
      header: "الحالة",
      cell: ({ getValue }) => String(getValue() || "-"),
    },
    {
      accessorKey: "date",
      header: "التاريخ",
      cell: ({ getValue }) => {
        const v = getValue();
        return v ? new Date(v as string).toLocaleDateString("ar-SA") : "-";
      },
    },
  ];

  const financialData = [
    ...(contracts?.map((c: Record<string, unknown>) => ({
      source: "عقد",
      ...c,
    })) || []),
    ...(invoices?.map((i: Record<string, unknown>) => ({
      source: "فاتورة",
      ...i,
    })) || []),
    ...(opportunities?.map((o: Record<string, unknown>) => ({
      source: "فرصة",
      ...o,
    })) || []),
  ];

  return (
    <div className="space-y-4">
      <Breadcrumbs items={breadcrumbItems} className="mb-2" />

      <div className="overflow-hidden rounded-xl border border-[var(--border-default)] bg-[var(--bg-primary)]">
        <div className="flex flex-wrap items-center gap-4 px-6 py-4">
          <Link
            href={`/companies/${id}`}
            className="flex h-14 w-14 items-center justify-center rounded-xl bg-[var(--muhide-orange)]/10 text-[var(--muhide-orange)] hover:bg-[var(--muhide-orange)]/20 transition-colors"
          >
            <Building2 className="h-7 w-7" />
          </Link>
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2">
              <h1 className="text-xl font-bold text-[var(--text-primary)]">
                {company.name_ar || company.name_en}
              </h1>
              <span className="rounded bg-purple-100 px-1.5 py-0.5 text-[10px] font-medium text-purple-700 dark:bg-purple-900/30 dark:text-purple-400">
                360
              </span>
            </div>
            <div className="mt-1 flex flex-wrap items-center gap-3 text-sm text-[var(--text-muted)]">
              {company.name_en && company.name_ar !== company.name_en && (
                <span>{company.name_en}</span>
              )}
              <span className="flex items-center gap-1">
                <FileText className="h-3.5 w-3.5" /> {company.cr_number}
              </span>
              {company.city && (
                <span className="flex items-center gap-1">
                  <MapPin className="h-3.5 w-3.5" /> {company.city}
                </span>
              )}
              <span
                className={cn(
                  "inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-xs font-medium",
                  company.status === "active"
                    ? "bg-success-50 text-success-700 dark:bg-success-900/30 dark:text-success-400"
                    : "bg-[var(--bg-tertiary)] text-[var(--text-secondary)]"
                )}
              >
                {company.status === "active" && <CheckCircle className="h-3 w-3" />}
                {company.status}
              </span>
            </div>
          </div>
          <HealthScoreRing score={healthScore} />
        </div>
      </div>

      <div className="flex flex-wrap items-center gap-2 rounded-xl border border-[var(--border-default)] bg-[var(--bg-primary)] px-3 py-2">
        <button
          onClick={() => setShowSampleData(!showSampleData)}
          className="px-3 py-1 text-xs rounded border border-[var(--border-default)] text-[var(--text-secondary)] hover:bg-[var(--bg-hover)]"
        >
          {showSampleData ? "إخفاء البيانات التجريبية" : "عرض بيانات تجريبية"}
        </button>
      </div>

      <div className="flex flex-wrap items-center gap-2 rounded-xl border border-[var(--border-default)] bg-[var(--bg-primary)] px-3 py-2">
        <span className="text-xs font-medium text-[var(--text-muted)]">إجراءات سريعة</span>
        <div className="flex flex-wrap gap-1.5">
          {QUICK_ACTIONS.map((action) => {
            const Icon = action.icon;
            return (
              <Link
                key={action.id}
                href={`/companies/${id}${action.href || ""}`}
                className={cn(
                  "inline-flex items-center gap-1.5 rounded-lg px-2.5 py-1.5 text-[11px] font-medium transition-colors hover:opacity-80",
                  action.color
                )}
              >
                <Icon className="h-3.5 w-3.5" />
                {action.label}
              </Link>
            );
          })}
        </div>
      </div>

      <Tabs value={activeTab} onValueChange={(v) => setActiveTab(v as TabId)}>
        <TabsList className="flex items-center gap-1 overflow-x-auto rounded-xl border border-[var(--border-default)] bg-[var(--bg-primary)] px-2 py-1">
          {TABS.map((tab) => {
            const Icon = tab.icon;
            return (
              <Tab
                key={tab.id}
                value={tab.id}
                className="flex items-center gap-1.5 whitespace-nowrap rounded-lg border-b-0 px-3 py-2 data-[state=active]:bg-[var(--muhide-orange)]/10 data-[state=active]:text-[var(--muhide-orange)] data-[state=active]:border-b-0"
              >
                <Icon className="h-4 w-4" />
                <span className="hidden sm:inline">{t(tab.labelKey)}</span>
              </Tab>
            );
          })}
        </TabsList>

        <TabsPanel value="overview">
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
              {overview?.total_revenue !== undefined && (
                <MetricBox
                  label="الإيرادات"
                  value={`$${(overview.total_revenue / 1000).toFixed(0)}K`}
                  icon={TrendingUp}
                  color="bg-success-50 text-success-700 dark:bg-success-900/20 dark:text-success-400"
                />
              )}
              {overview?.active_contracts !== undefined && (
                <MetricBox
                  label="العقود النشطة"
                  value={overview.active_contracts}
                  icon={FileText}
                  color="bg-info-50 text-info-700 dark:bg-info-900/20 dark:text-info-400"
                />
              )}
              {overview?.total_contacts !== undefined && (
                <MetricBox
                  label="جهات الاتصال"
                  value={overview.total_contacts}
                  icon={Users}
                  color="bg-purple-50 text-purple-700 dark:bg-purple-900/20 dark:text-purple-400"
                />
              )}
              {overview?.total_opportunities !== undefined && (
                <MetricBox
                  label="الفرص"
                  value={overview.total_opportunities}
                  icon={BarChart3}
                  color="bg-warning-50 text-warning-700 dark:bg-warning-900/20 dark:text-warning-400"
                />
              )}
            </div>
            <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
              <ErrorBoundary>
                <DecisionPlatformPanel companyId={id} company360={company360} />
              </ErrorBoundary>
              <Card>
                <CardHeader>
                  <div className="flex items-center gap-2">
                    <DollarSign className="h-5 w-5 text-[var(--text-muted)]" />
                    <span className="text-sm font-semibold text-[var(--text-primary)]">
                      البيانات المالية والإثراء
                    </span>
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="mb-4 grid grid-cols-2 gap-3 sm:grid-cols-4">
                    {enrichmentData.map((d) => (
                      <div key={d.label} className="rounded-lg bg-[var(--bg-secondary)] p-3">
                        <p className="text-[10px] text-[var(--text-muted)]">{d.label}</p>
                        <p className="mt-0.5 text-sm font-semibold text-[var(--text-primary)]">
                          {String(d.value)}
                        </p>
                      </div>
                    ))}
                  </div>
                  <DataTable
                    columns={financialColumns}
                    data={financialData}
                    emptyState={{
                      icon: <DollarSign className="h-10 w-10" />,
                      title: "لا توجد بيانات مالية",
                      description: "لم يتم العثور على عقود أو فواتير أو فرص لهذه الشركة",
                    }}
                  />
                </CardContent>
              </Card>
            </div>
          </div>
        </TabsPanel>

        <TabsPanel value="people">
          <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
            <Card>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Users className="h-5 w-5 text-[var(--text-muted)]" />
                    <span className="text-sm font-semibold text-[var(--text-primary)]">
                      جهات الاتصال
                    </span>
                  </div>
                  <Link
                    href={`/companies/${id}?action=add-contact`}
                    className="inline-flex items-center gap-1 rounded-lg bg-[var(--muhide-orange)]/10 px-2 py-1 text-[11px] font-medium text-[var(--muhide-orange)] hover:bg-[var(--muhide-orange)]/20 transition-colors"
                  >
                    <Plus className="h-3 w-3" />
                    إضافة
                  </Link>
                </div>
              </CardHeader>
              <CardContent>
                {showSampleData ? (
                  <div className="space-y-3">
                    {[
                      { name: "أحمد محمد", role: "المدير التنفيذي", email: "ahmed@example.com" },
                      { name: "سارة عبدالله", role: "مديرة المشتريات", email: "sara@example.com" },
                      { name: "خالد العتيبي", role: "مدير تقنية المعلومات", email: "khaled@example.com" },
                    ].map((c) => (
                      <div key={c.email} className="flex items-center gap-3 p-3 rounded-lg border border-[var(--border-default)]">
                        <div className="w-10 h-10 rounded-full bg-[var(--muhide-orange)]/20 flex items-center justify-center text-[var(--muhide-orange)] font-semibold">
                          {c.name.charAt(0)}
                        </div>
                        <div>
                          <div className="font-medium text-[var(--text-primary)]">{c.name}</div>
                          <div className="text-sm text-[var(--text-secondary)]">{c.role}</div>
                          <div className="text-xs text-[var(--text-muted)]">{c.email}</div>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <EmptyState
                    icon={<Users className="h-10 w-10" />}
                    title="لا توجد جهات اتصال"
                    description="ستظهر جهات الاتصال المرتبطة بالشركة هنا"
                  />
                )}
              </CardContent>
            </Card>
            {hierarchySections.length > 0 ? (
              hierarchySections.map((section) => (
                <Card key={section.title}>
                  <CardHeader>
                    <div className="flex items-center gap-2">
                      <section.icon className="h-5 w-5 text-[var(--text-muted)]" />
                      <span className="text-sm font-semibold text-[var(--text-primary)]">
                        {section.title}
                      </span>
                    </div>
                  </CardHeader>
                  <CardContent>
                    {section.items.length === 0 ? (
                      <EmptyState
                        icon={<section.icon className="h-8 w-8" />}
                        title={`لا توجد ${section.title}`}
                        description={`لم يتم العثور على ${section.title}`}
                      />
                    ) : (
                      <div className="space-y-1">
                        {section.items.map(
                          (item: { id: string; label: string; subtitle?: string }) => (
                            <div
                              key={item.id}
                              className="flex items-center gap-3 rounded-lg px-3 py-2 hover:bg-[var(--bg-secondary)] dark:hover:bg-[var(--bg-secondary)]/50"
                            >
                              <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-[var(--bg-tertiary)] text-[var(--text-secondary)]">
                                <section.icon className="h-4 w-4" />
                              </div>
                              <div>
                                <p className="text-sm font-medium text-[var(--text-primary)]">
                                  {item.label}
                                </p>
                                {item.subtitle && (
                                  <p className="text-xs text-[var(--text-muted)]">
                                    {item.subtitle}
                                  </p>
                                )}
                              </div>
                            </div>
                          )
                        )}
                      </div>
                    )}
                  </CardContent>
                </Card>
              ))
            ) : (
              <div className="lg:col-span-2">
                <Card>
                  <CardContent>
                    <EmptyState
                      icon={<Share2 className="h-10 w-10" />}
                      title="لا تبيانات هرمية"
                      description="لا توجد معلومات هرمية أو فروع لهذه الشركة"
                    />
                  </CardContent>
                </Card>
              </div>
            )}
            <KnowledgeGraphPanel companyId={id} />
          </div>
        </TabsPanel>

        <TabsPanel value="dealroom">
          <div className="space-y-4">
            <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
              <Card>
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <Handshake className="h-5 w-5 text-[var(--text-muted)]" />
                      <span className="text-sm font-semibold text-[var(--text-primary)]">
                        الصفقات النشطة
                      </span>
                    </div>
                    <Link
                      href={`/companies/${id}?action=new-deal`}
                      className="inline-flex items-center gap-1 rounded-lg bg-[var(--muhide-orange)]/10 px-2 py-1 text-[11px] font-medium text-[var(--muhide-orange)] hover:bg-[var(--muhide-orange)]/20 transition-colors"
                    >
                      <Plus className="h-3 w-3" />
                      صفقة جديدة
                    </Link>
                  </div>
                </CardHeader>
                <CardContent>
                  {showSampleData ? (
                    <div className="space-y-3">
                      {[
                        { name: "عقد خدمات استشارية", value: "450,000 ر.س", stage: "تفاوض", probability: "65%" },
                        { name: "ترخيص منصة رقمية", value: "280,000 ر.س", stage: "عرض سعر", probability: "40%" },
                        { name: "خدمات سحابية سنوية", value: "120,000 ر.س", stage: "مغلق-مكسب", probability: "100%" },
                      ].map((d) => (
                        <div key={d.name} className="flex items-center justify-between p-3 rounded-lg border border-[var(--border-default)]">
                          <div>
                            <div className="font-medium text-[var(--text-primary)]">{d.name}</div>
                            <div className="text-sm text-[var(--text-secondary)]">{d.stage}</div>
                          </div>
                          <div className="text-right">
                            <div className="font-semibold text-[var(--text-primary)]">{d.value}</div>
                            <div className="text-xs text-[var(--muhide-orange)]">{d.probability}</div>
                          </div>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <EmptyState
                      icon={<Handshake className="h-10 w-10" />}
                      title="لا توجد صفقات نشطة"
                      description="ستظهر الصفقات النشطة والمغلقة هنا"
                    />
                  )}
                </CardContent>
              </Card>
              <Card>
                <CardHeader>
                  <div className="flex items-center gap-2">
                    <FileText className="h-5 w-5 text-[var(--text-muted)]" />
                    <span className="text-sm font-semibold text-[var(--text-primary)]">
                      الوثائق
                    </span>
                  </div>
                </CardHeader>
                <CardContent>
                  {showSampleData ? (
                    <div className="space-y-3">
                      {[
                        { name: "اتفاقية شراكة استراتيجية", type: "PDF", date: "2026-06-15" },
                        { name: "شهادة تسجيل تجاري", type: "PDF", date: "2026-01-10" },
                        { name: "عرض تقديمي للخدمات", type: "PDF", date: "2026-05-20" },
                      ].map((doc) => (
                        <div key={doc.name} className="flex items-center gap-3 p-3 rounded-lg border border-[var(--border-default)]">
                          <FileText className="h-8 w-8 text-[var(--muhide-orange)]/70" />
                          <div>
                            <div className="font-medium text-[var(--text-primary)]">{doc.name}</div>
                            <div className="text-xs text-[var(--text-muted)]">{doc.type} · {doc.date}</div>
                          </div>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <EmptyState
                      icon={<FileText className="h-10 w-10" />}
                      title="لا توجد وثائق"
                      description="ستظهر المستندات والعقود المرتبطة بالشركة هنا"
                    />
                  )}
                </CardContent>
              </Card>
            </div>
            <Card>
              <CardHeader>
                <div className="flex items-center gap-2">
                  <Target className="h-5 w-5 text-[var(--text-muted)]" />
                  <span className="text-sm font-semibold text-[var(--text-primary)]">
                    الخطوات التالية
                  </span>
                </div>
              </CardHeader>
              <CardContent>
                {showSampleData ? (
                  <div className="space-y-3">
                    {[
                      { text: "متابعة عرض السعر المرسل", priority: "عاجل", dueDate: "2026-08-10" },
                      { text: "ترتيب اجتماع مع المدير المالي", priority: "متوسط", dueDate: "2026-08-15" },
                      { text: "إرسال مسودة العقد للمراجعة", priority: "منخفض", dueDate: "2026-08-20" },
                    ].map((step) => (
                      <div key={step.text} className="flex items-center justify-between p-3 rounded-lg border border-[var(--border-default)]">
                        <div className="flex items-center gap-3">
                          <input type="checkbox" className="rounded border-[var(--border-default)]" />
                          <div>
                            <div className="font-medium text-[var(--text-primary)]">{step.text}</div>
                            <div className="text-xs text-[var(--text-muted)]">{step.dueDate}</div>
                          </div>
                        </div>
                        <span className={cn(
                          "px-2 py-0.5 rounded-full text-[10px] font-medium",
                          step.priority === "عاجل" ? "bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400" :
                          step.priority === "متوسط" ? "bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400" :
                          "bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400"
                        )}>
                          {step.priority}
                        </span>
                      </div>
                    ))}
                  </div>
                ) : (
                  <EmptyState
                    icon={<Target className="h-10 w-10" />}
                    title="لا توجد خطوات تالية"
                    description="لم يتم تحديد خطوات تالية لهذه الشركة"
                  />
                )}
              </CardContent>
            </Card>
          </div>
        </TabsPanel>

        <TabsPanel value="activity">
          <ErrorBoundary>
            <ActivityTimeline companyId={id} />
          </ErrorBoundary>
        </TabsPanel>

        <TabsPanel value="more">
          <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
            <Card>
              <CardHeader>
                <div className="flex items-center gap-2">
                  <FileText className="h-5 w-5 text-[var(--text-muted)]" />
                  <span className="text-sm font-semibold text-[var(--text-primary)]">الوثائق</span>
                </div>
              </CardHeader>
              <CardContent>
                {showSampleData ? (
                  <div className="space-y-3">
                    {[
                      { name: "اتفاقية شراكة استراتيجية", type: "PDF", date: "2026-06-15" },
                      { name: "شهادة تسجيل تجاري", type: "PDF", date: "2026-01-10" },
                      { name: "عرض تقديمي للخدمات", type: "PDF", date: "2026-05-20" },
                    ].map((doc) => (
                      <div key={doc.name} className="flex items-center gap-3 p-3 rounded-lg border border-[var(--border-default)]">
                        <FileText className="h-8 w-8 text-[var(--muhide-orange)]/70" />
                        <div>
                          <div className="font-medium text-[var(--text-primary)]">{doc.name}</div>
                          <div className="text-xs text-[var(--text-muted)]">{doc.type} · {doc.date}</div>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <EmptyState
                    icon={<FileText className="h-10 w-10" />}
                    title="لا توجد وثائق"
                    description="ستظهر المستندات والعقود المرتبطة بالشركة هنا"
                  />
                )}
              </CardContent>
            </Card>
            <Card>
              <CardHeader>
                <div className="flex items-center gap-2">
                  <Bell className="h-5 w-5 text-[var(--text-muted)]" />
                  <span className="text-sm font-semibold text-[var(--text-primary)]">الإشارات</span>
                </div>
              </CardHeader>
              <CardContent>
                {showSampleData ? (
                  <div className="space-y-3">
                    {[
                      { title: "توسع إقليمي متوقع", description: "الشركة تخطط لفتح فروع جديدة في الرياض وجدة", type: "توسع" },
                      { title: "مشروع تحول رقمي", description: "إعلان عن مناقصة للتحول الرقمي بقيمة 50 مليون ر.س", type: "فرصة" },
                      { title: "تغيير إداري", description: "تعيين رئيس تنفيذي جديد للشركة", type: "تحديث" },
                    ].map((signal) => (
                      <div key={signal.title} className="p-3 rounded-lg border border-[var(--border-default)]">
                        <div className="flex items-start justify-between">
                          <Bell className="h-4 w-4 text-[var(--muhide-orange)] mt-0.5" />
                          <span className="text-[10px] px-1.5 py-0.5 rounded bg-[var(--bg-tertiary)] text-[var(--text-muted)]">
                            {signal.type}
                          </span>
                        </div>
                        <div className="mt-1 font-medium text-[var(--text-primary)]">{signal.title}</div>
                        <div className="mt-0.5 text-sm text-[var(--text-secondary)]">{signal.description}</div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <EmptyState
                    icon={<Bell className="h-10 w-10" />}
                    title="لا توجد إشارات"
                    description="لم يتم العثور على إشارات لهذه الشركة"
                  />
                )}
              </CardContent>
            </Card>
            <Card>
              <CardHeader>
                <div className="flex items-center gap-2">
                  <Settings className="h-5 w-5 text-[var(--text-muted)]" />
                  <span className="text-sm font-semibold text-[var(--text-primary)]">
                    الإعدادات
                  </span>
                </div>
              </CardHeader>
              <CardContent>
                <EmptyState
                  icon={<Settings className="h-10 w-10" />}
                  title="إعدادات الشركة"
                  description="إدارة إعدادات الشركة والصلاحيات"
                />
              </CardContent>
            </Card>
            <KnowledgeGraphPanel companyId={id} />
          </div>
        </TabsPanel>
      </Tabs>
    </div>
  );
}
