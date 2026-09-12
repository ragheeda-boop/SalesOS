"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";
import { createPipeline, type CreatePipelineResponse } from "@/lib/api";
import { pipelineKeys } from "@/lib/queryKeys";
import { getTenantId } from "@/lib/hooks/useTenant";

function createErrorMessage(err: unknown): string {
  if (err && typeof err === "object" && "response" in err) {
    const res = (
      err as { response?: { status?: number; data?: { detail?: unknown } } }
    ).response;
    if (res?.status === 403) return "You don't have permission to create pipelines.";
    const detail = res?.data?.detail;
    if (typeof detail === "string" && detail.trim()) return detail;
  }
  if (err instanceof Error && err.message) return err.message;
  return "Could not create pipeline.";
}

export function CreatePipelineButton() {
  const queryClient = useQueryClient();

  const createMutation = useMutation({
    mutationFn: () => createPipeline(getTenantId()),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: pipelineKeys.lists() });
    },
  });

  const created = createMutation.data as CreatePipelineResponse | undefined;

  return (
    <div
      className="space-y-2 rounded-[var(--radius-lg)] border border-[var(--border-default)] bg-[var(--bg-primary)] p-4"
      data-testid="create-pipeline-panel"
    >
      <h2 className="text-sm font-medium text-[var(--text-primary)]">Default sales pipeline</h2>
      <p className="text-[12px] text-[var(--text-muted)]">
        POST /api/v1/pipelines — no body. The API creates the default sales pipeline. There is no
        name or stages designer.
      </p>
      <button
        type="button"
        onClick={() => {
          if (createMutation.isPending) return;
          createMutation.mutate();
        }}
        disabled={createMutation.isPending}
        className="rounded-[var(--radius-md)] bg-[var(--muhide-orange)] px-3 py-1.5 text-sm font-medium text-white hover:opacity-90 disabled:opacity-50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--focus-ring)]"
        data-testid="create-pipeline-submit"
      >
        {createMutation.isPending ? "Creating…" : "Create default sales pipeline"}
      </button>
      {createMutation.isError ? (
        <p className="text-sm text-[var(--status-danger,#991b1b)]" role="alert">
          {createErrorMessage(createMutation.error)}
        </p>
      ) : null}
      {created?.id ? (
        <p className="text-sm text-[var(--text-secondary)]" data-testid="create-pipeline-result">
          Created {created.name?.trim() || "pipeline"} ({created.id}
          {Array.isArray(created.stages) && created.stages.length
            ? ` · ${created.stages.length} stages`
            : ""}
          ). Stays on this CRM board — no pipeline designer.
        </p>
      ) : null}
    </div>
  );
}
