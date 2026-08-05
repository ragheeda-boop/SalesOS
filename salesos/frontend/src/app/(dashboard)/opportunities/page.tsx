"use client";

import { PipelineKanban } from "@/components/pipeline-kanban";
import { ErrorBoundary } from "@/components/error-boundary";

export default function OpportunitiesPage() {
  return (
    <div className="mx-auto max-w-7xl">
      <ErrorBoundary>
        <PipelineKanban />
      </ErrorBoundary>
    </div>
  );
}
