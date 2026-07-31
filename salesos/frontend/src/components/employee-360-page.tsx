"use client";

import { useState, useMemo, lazy, Suspense } from "react";
import { useEmployee360 } from "@/lib/hooks/employeeQueries";
import {
  Tabs,
  TabsList,
  Tab,
  TabsPanel,
  Skeleton,
  EmptyState,
  cn,
} from "@salesos/ui";
import { User, Activity, Brain, Clock, TrendingUp } from "lucide-react";
import { useTranslation } from "@/lib/i18n";

const EmployeeOverview = lazy(() =>
  import("@/components/employee-360/employee-360-overview").then((m) => ({
    default: m.EmployeeOverview,
  })),
);
const EmployeeSignals = lazy(() =>
  import("@/components/employee-360/employee-360-signals").then((m) => ({
    default: m.EmployeeSignals,
  })),
);
const EmployeeScoring = lazy(() =>
  import("@/components/employee-360/employee-360-scoring").then((m) => ({
    default: m.EmployeeScoring,
  })),
);
const EmployeeTimeline = lazy(() =>
  import("@/components/employee-360/employee-360-timeline").then((m) => ({
    default: m.EmployeeTimeline,
  })),
);
const EmployeePerformance = lazy(() =>
  import("@/components/employee-360/employee-360-performance").then((m) => ({
    default: m.EmployeePerformance,
  })),
);

function TabFallback() {
  return <Skeleton className="h-64 rounded-xl" />;
}

type TabId = "overview" | "signals" | "scoring" | "timeline" | "performance";

const TABS: { id: TabId; labelKey: string; icon: typeof Activity }[] = [
  { id: "overview", labelKey: "emp360.tabs.overview", icon: User },
  { id: "signals", labelKey: "emp360.tabs.signals", icon: Activity },
  { id: "scoring", labelKey: "emp360.tabs.scoring", icon: Brain },
  { id: "timeline", labelKey: "emp360.tabs.timeline", icon: Clock },
  { id: "performance", labelKey: "emp360.tabs.performance", icon: TrendingUp },
];

interface Employee360PageProps {
  employeeId: string;
}

export function Employee360Page({ employeeId }: Employee360PageProps) {
  const { t } = useTranslation();
  const { data, isLoading, isError, error } = useEmployee360(employeeId);
  const [activeTab, setActiveTab] = useState<TabId>("overview");
  const [visitedTabs, setVisitedTabs] = useState<Set<TabId>>(
    new Set(["overview"]),
  );

  const handleTabChange = (v: string) => {
    const tabId = v as TabId;
    setActiveTab(tabId);
    setVisitedTabs((prev) => new Set(prev).add(tabId));
  };

  const baseData = useMemo(() => data as any, [data]);

  if (isLoading) {
    return (
      <div className="space-y-4">
        <Skeleton className="h-5 w-48" />
        <Skeleton className="h-40" />
        <div className="h-10 rounded-lg bg-[var(--bg-tertiary)]" />
        <Skeleton className="h-64 rounded-xl" />
      </div>
    );
  }

  if (isError || !data) {
    return (
      <div className="py-20">
        <EmptyState
          icon={<User className="h-12 w-12" />}
          title={t("emp360.load_error")}
          description={(error as Error)?.message || t("emp360.load_error_hint")}
          action={{
            label: t("common.back"),
            onClick: () => window.history.back(),
          }}
        />
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <Tabs value={activeTab} onValueChange={handleTabChange}>
        <TabsList className="flex items-center gap-1 overflow-x-auto rounded-xl border border-[var(--border-default)] bg-[var(--bg-primary)] px-2 py-1">
          {TABS.map((tab) => {
            const Icon = tab.icon;
            return (
              <Tab
                key={tab.id}
                value={tab.id}
                className={cn(
                  "flex items-center gap-1.5 whitespace-nowrap rounded-lg border-b-0 px-3 py-2",
                  "data-[state=active]:bg-[var(--muhide-orange)]/10 data-[state=active]:text-[var(--muhide-orange)] data-[state=active]:border-b-0",
                )}
              >
                <Icon className="h-4 w-4" />
                <span className="hidden sm:inline">{t(tab.labelKey)}</span>
              </Tab>
            );
          })}
        </TabsList>

        <TabsPanel value="overview">
          <Suspense fallback={<TabFallback />}>
            {visitedTabs.has("overview") && (
              <EmployeeOverview employeeId={employeeId} data={baseData} />
            )}
          </Suspense>
        </TabsPanel>

        <TabsPanel value="signals">
          <Suspense fallback={<TabFallback />}>
            {visitedTabs.has("signals") && (
              <EmployeeSignals employeeId={employeeId} />
            )}
          </Suspense>
        </TabsPanel>

        <TabsPanel value="scoring">
          <Suspense fallback={<TabFallback />}>
            {visitedTabs.has("scoring") && (
              <EmployeeScoring employeeId={employeeId} />
            )}
          </Suspense>
        </TabsPanel>

        <TabsPanel value="timeline">
          <Suspense fallback={<TabFallback />}>
            {visitedTabs.has("timeline") && (
              <EmployeeTimeline employeeId={employeeId} />
            )}
          </Suspense>
        </TabsPanel>

        <TabsPanel value="performance">
          <Suspense fallback={<TabFallback />}>
            {visitedTabs.has("performance") && (
              <EmployeePerformance employeeId={employeeId} />
            )}
          </Suspense>
        </TabsPanel>
      </Tabs>
    </div>
  );
}

export {
  ScoreBadge,
  formatRelativeTime,
} from "@/components/employee-360/employee-360-shared";
