"use client";

import { useState } from "react";
import { useCompany } from "@/lib/hooks/companyQueries";
import { useCompany360 } from "@/lib/hooks/company360Queries";
import { Avatar, cn, Tabs, TabsList, Tab, TabsPanel } from "@salesos/ui";
import { AI_ACTIONS, type AIAction } from "@salesos/design-language";
import {
  Building2,
  MapPin,
  FileText,
  Users,
  Sparkles,
  Activity,
  Zap,
  Shield,
  TrendingUp,
  BarChart3,
  AlertTriangle,
  CheckCircle,
  Clock,
} from "lucide-react";
import { useTranslation } from "@/lib/i18n";

import { SmartTimelineWidget } from "@/features/company-intelligence/widgets/smart-timeline/SmartTimelineContainer";
import { SignalsFeedWidget } from "@/features/company-intelligence/widgets/signals-feed/SignalsFeedContainer";
import { DecisionMakersWidget } from "@/features/company-intelligence/widgets/decision-makers/DecisionMakersContainer";
import { RelationshipGraphWidget } from "@/features/company-intelligence/widgets/relationship-graph/RelationshipGraphContainer";
import { AIRecommendationWidget } from "@/features/company-intelligence/widgets/ai-recommendation/AIRecommendationContainer";
import { CompanyDNAWidget } from "@/features/company-intelligence/widgets/company-dna/CompanyDNAContainer";
import { GovernmentIntelligenceWidget } from "@/features/company-intelligence/widgets/government-intelligence/GovernmentIntelligenceContainer";
import { DocumentIntelligenceWidget } from "@/features/company-intelligence/widgets/document-intelligence/DocumentIntelligenceContainer";
import { BuyingJourneyWidget } from "@/features/company-intelligence/widgets/buying-journey/BuyingJourneyContainer";
import { GoldenRecordWidget } from "@/features/company-intelligence/widgets/golden-record/GoldenRecordContainer";
import { TimelineWidget } from "./timeline-widget";

interface CompanyWorkspaceProps {
  companyId: string;
}

type TabId =
  | "overview"
  | "intelligence"
  | "contacts"
  | "government"
  | "documents"
  | "timeline"
  | "ai";

const TABS: { id: TabId; labelKey: string; icon: typeof Activity }[] = [
  { id: "overview", labelKey: "tabs.overview", icon: BarChart3 },
  { id: "intelligence", labelKey: "tabs.intelligence", icon: Sparkles },
  { id: "contacts", labelKey: "tabs.decision_makers", icon: Users },
  { id: "government", labelKey: "tabs.government_data", icon: Shield },
  { id: "documents", labelKey: "tabs.documents", icon: FileText },
  { id: "timeline", labelKey: "tabs.timeline", icon: Clock },
  { id: "ai", labelKey: "AI", icon: Sparkles },
];

function HealthScoreRing({ score, label }: { score: number; label: string }) {
  const radius = 28;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (score / 100) * circumference;
  const color = score >= 70 ? "#22c55e" : score >= 40 ? "#f59e0b" : "#ef4444";

  return (
    <div className="relative flex items-center justify-center">
      <svg width="68" height="68" viewBox="0 0 68 68">
        <circle
          cx="34"
          cy="34"
          r={radius}
          fill="none"
          stroke="currentColor"
          className="text-[var(--text-primary)]"
          strokeWidth="5"
        />
        <circle
          cx="34"
          cy="34"
          r={radius}
          fill="none"
          stroke={color}
          strokeWidth="5"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          strokeLinecap="round"
          transform="rotate(-90 34 34)"
          className="transition-all duration-700"
        />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span className="text-lg font-bold text-[var(--text-primary)]">
          {score}
        </span>
        <span className="text-[8px] text-[var(--text-muted)]">{label}</span>
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
  value: string | number;
  icon: typeof Activity;
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

export function CompanyWorkspace({ companyId }: CompanyWorkspaceProps) {
  const { t } = useTranslation();
  const { data: company, isLoading, isError } = useCompany(companyId);
  const { data: company360 } = useCompany360(companyId);
  const [activeTab, setActiveTab] = useState<TabId>("overview");

  const healthScore =
    company360?.health_score || company?.confidence_score || 0;

  if (isLoading) {
    return (
      <div className="space-y-4">
        <div className="h-32 animate-pulse rounded-xl bg-[var(--bg-tertiary)]" />
        <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
          {Array.from({ length: 4 }).map((_, i) => (
            <div
              key={i}
              className="h-20 animate-pulse rounded-xl bg-[var(--bg-tertiary)]"
            />
          ))}
        </div>
        <div className="h-96 animate-pulse rounded-xl bg-[var(--bg-tertiary)]" />
      </div>
    );
  }

  if (isError || !company) {
    return (
      <div className="flex flex-col items-center justify-center py-20 text-center">
        <AlertTriangle className="mb-3 h-10 w-10 text-danger-500" />
        <p className="text-lg font-semibold text-[var(--text-primary)]">
          {t("company.load_error")}
        </p>
        <p className="mt-1 text-sm text-[var(--text-muted)]">
          {t("company.load_error_hint")}
        </p>
      </div>
    );
  }

  const overview = company360?.overview;
  const assignedEmployees = company360?.assigned_employees || [];
  const opportunities = company360?.opportunities || [];

  return (
    <div className="space-y-4">
      {/* Company Header */}
      <div className="overflow-hidden rounded-xl border border-[var(--border-default)] bg-[var(--bg-primary)] shadow-muhide-1">
        <div className="flex flex-wrap items-center gap-4 px-6 py-4">
          <div className="flex h-14 w-14 items-center justify-center rounded-xl bg-info-100 text-info-700 dark:bg-info-900 dark:text-info-300">
            <Building2 className="h-7 w-7" />
          </div>
          <div className="flex-1 min-w-0">
            <h1 className="text-xl font-bold text-[var(--text-primary)]">
              {company.name_ar || company.name_en}
            </h1>
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
              {company.region && (
                <span className="text-xs text-[var(--text-disabled)]">
                  {company.region}
                </span>
              )}
              <span
                className={cn(
                  "inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-xs font-medium",
                  company.status === "active"
                    ? "bg-success-50 text-success-700 dark:bg-success-900/30 dark:text-success-400"
                    : "bg-[var(--bg-tertiary)] text-[var(--text-secondary)]",
                )}
              >
                {company.status === "active" && (
                  <CheckCircle className="h-3 w-3" />
                )}
                {company.status}
              </span>
            </div>
          </div>
          <HealthScoreRing score={healthScore} label={t("company.health")} />
        </div>

        {/* AI Action Bar */}
        <div className="flex items-center gap-1 border-t border-[var(--border-subtle)] px-6 py-2">
          <Sparkles className="h-3.5 w-3.5 text-[var(--chart-purple)]" />
          <span className="ms-1 text-[10px] font-medium text-[var(--text-disabled)]">
            AI:
          </span>
          {(
            [
              "explain",
              "analyze",
              "predict",
              "summarize",
              "recommend",
            ] as AIAction[]
          ).map((actionId) => {
            const action = AI_ACTIONS[actionId];
            return (
              <button
                key={actionId}
                className="flex items-center gap-1 rounded-lg px-2 py-1 text-[10px] text-[var(--chart-purple)] hover:bg-[var(--chart-purple-bg)] dark:text-[var(--chart-purple)] dark:hover:bg-[var(--bg-primary)]/50 transition-colors"
              >
                {action.labelAr}
              </button>
            );
          })}
        </div>
      </div>

      {/* Quick Metrics */}
      {(overview ||
        assignedEmployees.length > 0 ||
        opportunities.length > 0) && (
        <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
          {overview?.total_revenue !== undefined && (
            <MetricCard
              label={t("company.revenue")}
              value={`$${(overview.total_revenue / 1000).toFixed(0)}K`}
              icon={TrendingUp}
              color="bg-success-50 text-success-700 dark:bg-success-900/20 dark:text-success-400"
            />
          )}
          {overview?.active_contracts !== undefined && (
            <MetricCard
              label={t("company.active_contracts")}
              value={overview.active_contracts}
              icon={BarChart3}
              color="bg-info-50 text-info-700 dark:bg-info-900/20 dark:text-info-400"
            />
          )}
          {assignedEmployees.length > 0 && (
            <MetricCard
              label={t("company.assigned_team")}
              value={assignedEmployees.length}
              icon={Users}
              color="bg-[var(--chart-purple-bg)] text-[var(--text-secondary)] dark:bg-[var(--bg-primary)]/20 dark:text-[var(--chart-purple)]"
            />
          )}
          {opportunities.length > 0 && (
            <MetricCard
              label={t("company.opportunities")}
              value={opportunities.length}
              icon={Zap}
              color="bg-warning-50 text-warning-700 dark:bg-warning-900/20 dark:text-warning-400"
            />
          )}
        </div>
      )}

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
            <TimelineWidget
              entityType="company"
              entityId={companyId}
              title={t("company.activity_log")}
            />
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
        <div className="rounded-xl border border-[var(--border-default)] bg-[var(--bg-primary)] p-4">
          <h3 className="mb-3 flex items-center gap-2 text-sm font-semibold text-[var(--text-primary)]">
            <Users className="h-4 w-4" />
            {t("company.assigned_team")}
          </h3>
          <div className="flex flex-wrap gap-2">
            {assignedEmployees.map(
              (emp: Record<string, unknown>, i: number) => (
                <div
                  key={i}
                  className="flex items-center gap-2 rounded-lg border border-[var(--border-default)] px-3 py-2 text-sm"
                >
                  <Avatar
                    size="sm"
                    fallback={String(emp.full_name || emp.name || "")
                      .split("")
                      .map((n: string) => n[0])
                      .join("")
                      .slice(0, 2)
                      .toUpperCase()}
                    className="h-7 w-7 text-xs"
                  />
                  <span className="text-[var(--text-primary)]">
                    {String(emp.full_name || emp.name)}
                  </span>
                  {emp.role ? (
                    <span className="text-xs text-[var(--text-muted)]">
                      {String(emp.role)}
                    </span>
                  ) : null}
                </div>
              ),
            )}
          </div>
        </div>
      )}
    </div>
  );
}
