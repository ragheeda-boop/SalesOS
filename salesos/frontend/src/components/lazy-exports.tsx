"use client";

import dynamic from "next/dynamic";
import type { ComponentType } from "react";

function PanelSkeleton({ label }: { label: string }) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/20">
      <div className="rounded-lg bg-[var(--bg-primary)] p-6 shadow-lg">
        <div className="h-4 w-32 animate-pulse rounded bg-[var(--bg-tertiary)]" />
        <p className="mt-2 text-xs text-[var(--text-muted)]">{label}</p>
      </div>
    </div>
  );
}

export const LazyCommandBar = dynamic(
  () => import("@/components/command-bar").then((m) => m.CommandBar),
  {
    ssr: false,
    loading: () => <PanelSkeleton label="Command bar loading..." />,
  },
) as ComponentType<{ open: boolean; onClose: () => void }>;

export const LazySearchPanel = dynamic(
  () => import("@/components/search-panel").then((m) => m.SearchPanel),
  {
    ssr: false,
    loading: () => <PanelSkeleton label="Search loading..." />,
  },
) as ComponentType<{ open: boolean; onClose: () => void }>;

export const LazyCopilotPanel = dynamic(
  () => import("@/components/copilot-panel").then((m) => m.CopilotPanel),
  {
    ssr: false,
    loading: () => <PanelSkeleton label="Copilot loading..." />,
  },
) as ComponentType<{ open: boolean; onClose: () => void; entityType: string }>;

export const LazyExecutiveDashboard = dynamic(
  () =>
    import("@/components/executive-dashboard").then(
      (m) => m.ExecutiveDashboard,
    ),
  {
    ssr: false,
    loading: () => (
      <div className="h-64 animate-pulse rounded-lg bg-[var(--bg-tertiary)]" />
    ),
  },
);

export const LazyTimelineWidget = dynamic(
  () => import("@/components/timeline-widget").then((m) => m.TimelineWidget),
  {
    ssr: false,
    loading: () => (
      <div className="h-48 animate-pulse rounded-lg bg-[var(--bg-tertiary)]" />
    ),
  },
);

export const LazyPipelineKanban = dynamic(
  () => import("@/components/pipeline-kanban").then((m) => m.PipelineKanban),
  {
    ssr: false,
    loading: () => (
      <div className="h-96 animate-pulse rounded-lg bg-[var(--bg-tertiary)]" />
    ),
  },
);

export const LazyCompanyWorkspace = dynamic(
  () =>
    import("@/components/company-workspace").then((m) => m.CompanyWorkspace),
  {
    ssr: false,
    loading: () => (
      <div className="h-96 animate-pulse rounded-lg bg-[var(--bg-tertiary)]" />
    ),
  },
);
