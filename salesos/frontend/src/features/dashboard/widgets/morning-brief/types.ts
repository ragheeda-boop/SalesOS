"use client";

export interface MorningBriefItem {
  id: string;
  type: "meeting" | "follow-up" | "task" | "deal" | "signal";
  title: string;
  companyName?: string;
  time?: string;
  priority: "high" | "medium" | "low";
  completed?: boolean;
}

export interface MorningBriefData {
  greeting: string;
  date: string;
  priorities: MorningBriefItem[];
  stats: {
    meetingsToday: number;
    pendingFollowUps: number;
    openTasks: number;
    atRiskDeals: number;
  };
}
