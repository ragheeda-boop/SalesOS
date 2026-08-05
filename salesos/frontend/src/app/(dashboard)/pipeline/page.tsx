"use client";

import { PipelineWorkspace } from "@/features/revenue-execution/workspace/pipeline/PipelineWorkspace";
import { ErrorBoundary } from "@/components/error-boundary";

export default function PipelinePage() {
  return (
    <div className="mx-auto max-w-[1600px] px-6 py-6">
      <ErrorBoundary>
        <PipelineWorkspace />
      </ErrorBoundary>
    </div>
  );
}
