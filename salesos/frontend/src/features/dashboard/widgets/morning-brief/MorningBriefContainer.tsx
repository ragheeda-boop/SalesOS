"use client";

import { useMemo } from "react";
import { Card, CardContent } from "@salesos/ui";
import { useDashboardContext } from "../../_providers/dashboard-provider";
import { MorningBriefView } from "./MorningBriefView";
import type { MorningBriefData, MorningBriefItem } from "./types";
import { Sun } from "lucide-react";

function buildMorningBriefFromWidgets(
  widgets: ReturnType<typeof useDashboardContext>["widgets"],
): MorningBriefData {
  const now = new Date();
  const hour = now.getHours();
  const greeting =
    hour < 12
      ? "صباح الخير"
      : hour < 18
        ? "مساء الخير"
        : "مساء الخير";

  const dateStr = now.toLocaleDateString("ar-SA", {
    weekday: "long",
    year: "numeric",
    month: "long",
    day: "numeric",
  });

  const priorities: MorningBriefItem[] = [];

  const decisions = widgets.decisionQueue?.data;
  if (decisions?.items) {
    decisions.items.slice(0, 5).forEach((item) => {
      priorities.push({
        id: item.id,
        type: item.type === "opportunity" ? "deal" : item.type === "risk" ? "deal" : "task",
        title: item.title,
        companyName: item.companyName,
        time: item.dueBy,
        priority: item.priority,
      });
    });
  }

  const followups = widgets.followupCenter?.data;
  if (followups) {
    const items = followups.items;
    if (Array.isArray(items)) {
      items.slice(0, 3).forEach((item) => {
        priorities.push({
          id: item.company_id,
          type: "follow-up",
          title: item.company_id,
          companyName: item.company_id,
          priority: item.priority === "critical" ? "high" : item.priority,
        });
      });
    }
  }

  const calendar = widgets.calendarIntelligence?.data;
  if (calendar) {
    const upcoming = calendar.upcoming;
    if (Array.isArray(upcoming)) {
      upcoming.slice(0, 3).forEach((item) => {
        priorities.push({
          id: String(Math.random()),
          type: "meeting",
          title: String(item.title ?? "اجتماع"),
          companyName: String(item.company_id ?? ""),
          time: item.start_time
            ? new Date(item.start_time).toLocaleTimeString("ar-SA", {
                hour: "2-digit",
                minute: "2-digit",
              })
            : "",
          priority: "high",
        });
      });
    }
  }

  priorities.sort((a, b) => {
    const order = { high: 0, medium: 1, low: 2 };
    return (order[a.priority] ?? 2) - (order[b.priority] ?? 2);
  });

  return {
    greeting,
    date: dateStr,
    priorities: priorities.slice(0, 8),
    stats: {
      meetingsToday: calendar?.meeting_count ?? 0,
      pendingFollowUps: followups?.need_followup ?? 0,
      openTasks: decisions?.total ?? 0,
      atRiskDeals: decisions?.items?.filter((i) => i.type === "risk").length ?? 0,
    },
  };
}

export function MorningBriefWidget() {
  const { widgets } = useDashboardContext();

  const briefData = useMemo(
    () => buildMorningBriefFromWidgets(widgets),
    [widgets],
  );

  return (
    <Card className="overflow-hidden border-[var(--muhide-orange)]/20 bg-gradient-to-br from-[var(--bg-primary)] to-orange-50/30 dark:to-orange-950/10">
      <CardContent className="p-5">
        <div className="flex items-center gap-2 mb-3">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-[var(--muhide-orange)]/10">
            <Sun className="h-4 w-4 text-[var(--muhide-orange)]" />
          </div>
          <span className="text-xs font-semibold text-[var(--muhide-orange)]">
            ملخص الصباح
          </span>
        </div>
        <MorningBriefView data={briefData} />
      </CardContent>
    </Card>
  );
}
