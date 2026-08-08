"use client";
/* eslint-disable custom-rules/no-tailwind-color-classes */

import { Card, CardContent, cn } from "@salesos/ui";
import { useDashboardContext } from "../../_providers/dashboard-provider";
import { DollarSign, TrendingUp, Users, ArrowUp, ArrowDown, Target } from "lucide-react";
import type { MissionCenterData } from "@/application/dashboard/dashboard.dto";

interface ExecCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  icon: React.ReactNode;
  bgColor: string;
  trend?: number;
  trendUp?: boolean;
}

function ExecCard({ title, value, subtitle, icon, bgColor, trend, trendUp }: ExecCardProps) {
  return (
    <Card className="overflow-hidden transition-all hover:shadow-muhide-2">
      <CardContent className="p-4">
        <div className="flex items-start justify-between">
          <div className="space-y-1 min-w-0 flex-1">
            <p className="text-xs font-medium text-[var(--text-muted)] truncate">{title}</p>
            <p className="text-2xl font-bold text-[var(--text-primary)] tabular-nums">{value}</p>
            {subtitle && <p className="text-xs text-[var(--text-muted)] truncate">{subtitle}</p>}
            {trend !== undefined && (
              <span
                className={cn(
                  "inline-flex items-center gap-0.5 text-xs font-medium",
                  trendUp ? "text-success-600" : "text-danger-600"
                )}
              >
                {trendUp ? <ArrowUp className="h-3 w-3" /> : <ArrowDown className="h-3 w-3" />}
                {trend}%
              </span>
            )}
          </div>
          <div
            className={cn(
              "flex h-10 w-10 shrink-0 items-center justify-center rounded-xl",
              bgColor
            )}
          >
            {icon}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

export function ExecutiveSummaryCards() {
  const { widgets } = useDashboardContext();
  const mission = widgets.missionCenter?.data as MissionCenterData | null;

  if (!mission) return null;

  const pipelineFormatted =
    mission.pipelineValue >= 1_000_000
      ? `${(mission.pipelineValue / 1_000_000).toFixed(1)}M`
      : mission.pipelineValue >= 1_000
        ? `${(mission.pipelineValue / 1_000).toFixed(0)}K`
        : String(mission.pipelineValue);

  const cards: ExecCardProps[] = [
    {
      title: "الشركات المُتتبَعة",
      value: mission.companiesTracked.toLocaleString(),
      icon: <Users className="h-5 w-5 text-info-600 dark:text-info-400" />,
      bgColor: "bg-info-100 dark:bg-info-950/30",
    },
    {
      title: "الصفقات النشطة",
      value: mission.activeDeals,
      subtitle: `${pipelineFormatted} قيمة الأنبوب`,
      icon: <DollarSign className="h-5 w-5 text-[var(--muhide-orange)]" />,
      bgColor: "bg-orange-100 dark:bg-orange-950/30",
    },
    {
      title: "قيمة الأنبوب",
      value: `${pipelineFormatted}`,
      icon: <TrendingUp className="h-5 w-5 text-success-600 dark:text-success-400" />,
      bgColor: "bg-success-100 dark:bg-success-950/30",
    },
    {
      title: "القرارات المُعلَّقة",
      value: mission.decisionsPending,
      icon: <Target className="h-5 w-5 text-purple-600 dark:text-purple-400" />,
      bgColor: "bg-purple-100 dark:bg-purple-950/30",
    },
  ];

  return (
    <div
      className="grid gap-3"
      style={{ gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))" }}
    >
      {cards.map((card) => (
        <ExecCard key={card.title} {...card} />
      ))}
    </div>
  );
}
