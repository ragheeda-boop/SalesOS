"use client"

import { useState, useMemo } from "react"
import { useCompany } from "@/lib/hooks/companyQueries"
import { useCompany360 } from "@/lib/hooks/company360Queries"
import { Avatar, cn, Tabs, TabsList, Tab, TabsPanel } from "@salesos/ui"
import { AI_ACTIONS, type AIAction } from "@salesos/design-language"
import {
  Building2, MapPin, FileText, Users, Sparkles, Activity, Zap, Share2,
  Shield, Briefcase, TrendingUp, ChevronLeft, Loader2, ExternalLink,
  BarChart3, Globe, Newspaper, AlertTriangle, CheckCircle, Clock,
} from "lucide-react"

import { SmartTimelineWidget } from "@/features/company-intelligence/widgets/smart-timeline/SmartTimelineContainer"
import { SignalsFeedWidget } from "@/features/company-intelligence/widgets/signals-feed/SignalsFeedContainer"
import { DecisionMakersWidget } from "@/features/company-intelligence/widgets/decision-makers/DecisionMakersContainer"
import { RelationshipGraphWidget } from "@/features/company-intelligence/widgets/relationship-graph/RelationshipGraphContainer"
import { AIRecommendationWidget } from "@/features/company-intelligence/widgets/ai-recommendation/AIRecommendationContainer"
import { CompanyDNAWidget } from "@/features/company-intelligence/widgets/company-dna/CompanyDNAContainer"
import { GovernmentIntelligenceWidget } from "@/features/company-intelligence/widgets/government-intelligence/GovernmentIntelligenceContainer"
import { DocumentIntelligenceWidget } from "@/features/company-intelligence/widgets/document-intelligence/DocumentIntelligenceContainer"
import { BuyingJourneyWidget } from "@/features/company-intelligence/widgets/buying-journey/BuyingJourneyContainer"
import { GoldenRecordWidget } from "@/features/company-intelligence/widgets/golden-record/GoldenRecordContainer"
import { TimelineWidget } from "./timeline-widget"

interface CompanyWorkspaceProps {
  companyId: string
}

type TabId = "overview" | "intelligence" | "contacts" | "government" | "documents" | "timeline" | "ai"

const TABS: { id: TabId; label: string; icon: typeof Activity }[] = [
  { id: "overview", label: "نظرة عامة", icon: BarChart3 },
  { id: "intelligence", label: "الذكاء", icon: Sparkles },
  { id: "contacts", label: "صناع القرار", icon: Users },
  { id: "government", label: "البيانات الحكومية", icon: Shield },
  { id: "documents", label: "المستندات", icon: FileText },
  { id: "timeline", label: "الجدول الزمني", icon: Clock },
  { id: "ai", label: "AI", icon: Sparkles },
]

function HealthScoreRing({ score }: { score: number }) {
  const radius = 28
  const circumference = 2 * Math.PI * radius
  const offset = circumference - (score / 100) * circumference
  const color = score >= 70 ? "#22c55e" : score >= 40 ? "#f59e0b" : "#ef4444"

  return (
    <div className="relative flex items-center justify-center">
      <svg width="68" height="68" viewBox="0 0 68 68">
        <circle cx="34" cy="34" r={radius} fill="none" stroke="currentColor" className="text-neutral-100 dark:text-neutral-800" strokeWidth="5" />
        <circle cx="34" cy="34" r={radius} fill="none" stroke={color} strokeWidth="5" strokeDasharray={circumference} strokeDashoffset={offset} strokeLinecap="round" transform="rotate(-90 34 34)" className="transition-all duration-700" />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span className="text-lg font-bold text-neutral-900 dark:text-neutral-100">{score}</span>
        <span className="text-[8px] text-neutral-500">صحة</span>
      </div>
    </div>
  )
}

function MetricCard({ label, value, icon: Icon, color }: { label: string; value: string | number; icon: typeof Activity; color: string }) {
  return (
    <div className={cn("flex items-center gap-3 rounded-xl p-3", color)}>
      <Icon className="h-5 w-5 shrink-0" />
      <div>
        <p className="text-[10px] opacity-70">{label}</p>
        <p className="text-sm font-bold">{value}</p>
      </div>
    </div>
  )
}

export function CompanyWorkspace({ companyId }: CompanyWorkspaceProps) {
  const { data: company, isLoading, isError } = useCompany(companyId)
  const { data: company360 } = useCompany360(companyId)
  const [activeTab, setActiveTab] = useState<TabId>("overview")

  const healthScore = company360?.health_score || company?.confidence_score || 0

  if (isLoading) {
    return (
      <div className="space-y-4">
        <div className="h-32 animate-pulse rounded-xl bg-neutral-100 dark:bg-neutral-800" />
        <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
          {Array.from({ length: 4 }).map((_, i) => (
            <div key={i} className="h-20 animate-pulse rounded-xl bg-neutral-100 dark:bg-neutral-800" />
          ))}
        </div>
        <div className="h-96 animate-pulse rounded-xl bg-neutral-100 dark:bg-neutral-800" />
      </div>
    )
  }

  if (isError || !company) {
    return (
      <div className="flex flex-col items-center justify-center py-20 text-center">
        <AlertTriangle className="mb-3 h-10 w-10 text-danger-500" />
        <p className="text-lg font-semibold text-neutral-900 dark:text-neutral-100">فشل تحميل بيانات الشركة</p>
        <p className="mt-1 text-sm text-neutral-500">تأكد من اتصال الخادم وحاول مرة أخرى</p>
      </div>
    )
  }

  const overview = company360?.overview
  const assignedEmployees = company360?.assigned_employees || []
  const opportunities = company360?.opportunities || []

  return (
    <div className="space-y-4">
      {/* Company Header */}
      <div className="overflow-hidden rounded-xl border border-neutral-200 bg-white shadow-muhide-1 dark:border-neutral-700 dark:bg-neutral-900">
        <div className="flex flex-wrap items-center gap-4 px-6 py-4">
          <div className="flex h-14 w-14 items-center justify-center rounded-xl bg-info-100 text-info-700 dark:bg-info-900 dark:text-info-300">
            <Building2 className="h-7 w-7" />
          </div>
          <div className="flex-1 min-w-0">
            <h1 className="text-xl font-bold text-neutral-900 dark:text-neutral-100">
              {company.name_ar || company.name_en}
            </h1>
            <div className="mt-1 flex flex-wrap items-center gap-3 text-sm text-neutral-500 dark:text-neutral-400">
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
              {company.region && (
                <span className="text-xs text-neutral-400">{company.region}</span>
              )}
              <span className={cn(
                "inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-xs font-medium",
                company.status === "active"
                  ? "bg-success-50 text-success-700 dark:bg-success-900/30 dark:text-success-400"
                  : "bg-neutral-100 text-neutral-600 dark:bg-neutral-800 dark:text-neutral-400"
              )}>
                {company.status === "active" && <CheckCircle className="h-3 w-3" />}
                {company.status}
              </span>
            </div>
          </div>
          <HealthScoreRing score={healthScore} />
        </div>

        {/* AI Action Bar */}
        <div className="flex items-center gap-1 border-t border-neutral-100 px-6 py-2 dark:border-neutral-800">
          <Sparkles className="h-3.5 w-3.5 text-purple-500" />
          <span className="ms-1 text-[10px] font-medium text-neutral-400">AI:</span>
          {(["explain", "analyze", "predict", "summarize", "recommend"] as AIAction[]).map((actionId) => {
            const action = AI_ACTIONS[actionId]
            return (
              <button
                key={actionId}
                className="flex items-center gap-1 rounded-lg px-2 py-1 text-[10px] text-purple-600 hover:bg-purple-50 dark:text-purple-400 dark:hover:bg-purple-900/50 transition-colors"
              >
                {action.labelAr}
              </button>
            )
          })}
        </div>
      </div>

      {/* Quick Metrics */}
      {(overview || assignedEmployees.length > 0 || opportunities.length > 0) && (
        <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
          {overview?.total_revenue !== undefined && (
            <MetricCard
              label="الإيرادات"
              value={`$${(overview.total_revenue / 1000).toFixed(0)}K`}
              icon={TrendingUp}
              color="bg-success-50 text-success-700 dark:bg-success-900/20 dark:text-success-400"
            />
          )}
          {overview?.active_contracts !== undefined && (
            <MetricCard
              label="العقود النشطة"
              value={overview.active_contracts}
              icon={BarChart3}
              color="bg-info-50 text-info-700 dark:bg-info-900/20 dark:text-info-400"
            />
          )}
          {assignedEmployees.length > 0 && (
            <MetricCard
              label="الفريق المعين"
              value={assignedEmployees.length}
              icon={Users}
              color="bg-purple-50 text-purple-700 dark:bg-purple-900/20 dark:text-purple-400"
            />
          )}
          {opportunities.length > 0 && (
            <MetricCard
              label="الفرص"
              value={opportunities.length}
              icon={Zap}
              color="bg-warning-50 text-warning-700 dark:bg-warning-900/20 dark:text-warning-400"
            />
          )}
        </div>
      )}

      <Tabs value={activeTab} onValueChange={(v) => setActiveTab(v as TabId)}>
        <TabsList className="flex items-center gap-1 overflow-x-auto rounded-xl border border-neutral-200 bg-white px-2 py-1 dark:border-neutral-700 dark:bg-neutral-900">
          {TABS.map((tab) => {
            const Icon = tab.icon
            return (
              <Tab
                key={tab.id}
                value={tab.id}
                className="flex items-center gap-1.5 whitespace-nowrap rounded-lg border-b-0 px-3 py-2 data-[state=active]:bg-[var(--muhide-orange)]/10 data-[state=active]:text-[var(--muhide-orange)] data-[state=active]:border-b-0 dark:data-[state=active]:bg-[var(--muhide-orange)]/20 dark:data-[state=active]:text-orange-300"
              >
                <Icon className="h-4 w-4" />
                <span className="hidden sm:inline">{tab.label}</span>
              </Tab>
            )
          })}
        </TabsList>

        <TabsPanel value="overview">
          <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
            <CompanyDNAWidget />
            <AIRecommendationWidget />
            <BuyingJourneyWidget />
            <RelationshipGraphWidget />
          </div>
        </TabsPanel>

        <TabsPanel value="intelligence">
          <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
            <SignalsFeedWidget />
            <SmartTimelineWidget />
          </div>
        </TabsPanel>

        <TabsPanel value="contacts">
          <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
            <DecisionMakersWidget />
            <RelationshipGraphWidget />
          </div>
        </TabsPanel>

        <TabsPanel value="government">
          <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
            <GovernmentIntelligenceWidget />
            <GoldenRecordWidget />
          </div>
        </TabsPanel>

        <TabsPanel value="documents">
          <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
            <DocumentIntelligenceWidget />
          </div>
        </TabsPanel>

        <TabsPanel value="timeline">
          <div className="space-y-4">
            <SmartTimelineWidget />
            <TimelineWidget entityType="company" entityId={companyId} title="سجل النشاطات" />
          </div>
        </TabsPanel>

        <TabsPanel value="ai">
          <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
            <AIRecommendationWidget />
            <BuyingJourneyWidget />
            <CompanyDNAWidget />
          </div>
        </TabsPanel>
      </Tabs>

      {/* Assigned Team */}
      {assignedEmployees.length > 0 && (
        <div className="rounded-xl border border-neutral-200 bg-white p-4 dark:border-neutral-700 dark:bg-neutral-900">
          <h3 className="mb-3 flex items-center gap-2 text-sm font-semibold text-neutral-900 dark:text-neutral-100">
            <Users className="h-4 w-4" />
            الفريق المعين
          </h3>
          <div className="flex flex-wrap gap-2">
            {assignedEmployees.map((emp: Record<string, unknown>, i: number) => (
              <div key={i} className="flex items-center gap-2 rounded-lg border border-neutral-200 px-3 py-2 text-sm dark:border-neutral-700">
                <Avatar
                  size="sm"
                  fallback={String(emp.full_name || emp.name || "").split(" ").map((n: string) => n[0]).join("").slice(0, 2).toUpperCase()}
                  className="h-7 w-7 text-xs"
                />
                <span className="text-neutral-900 dark:text-neutral-100">{String(emp.full_name || emp.name)}</span>
                {emp.role ? <span className="text-xs text-neutral-500">{String(emp.role)}</span> : null}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
