"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  compileWorkflowCanvas,
  compileWorkflowCanvasEphemeral,
  listWorkflowCanvases,
  upsertWorkflowCanvas,
  type WorkflowCanvasUpsert,
} from "@/lib/api";
import { tenantStudioKeys } from "@/lib/queryKeys";
import { getTenantId } from "./useTenant";

export function useWorkflowCanvases() {
  const tenantId = getTenantId();
  return useQuery({
    queryKey: tenantStudioKeys.workflows(tenantId),
    queryFn: () => listWorkflowCanvases(tenantId),
    staleTime: 10_000,
  });
}

export function useUpsertWorkflowCanvas() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body: WorkflowCanvasUpsert) => upsertWorkflowCanvas(getTenantId(), body),
    onSuccess: () => {
      qc.invalidateQueries({
        queryKey: tenantStudioKeys.workflows(getTenantId()),
      });
    },
  });
}

export function useCompileWorkflowCanvas() {
  return useMutation({
    mutationFn: (canvasId: string) => compileWorkflowCanvas(getTenantId(), canvasId),
  });
}

export function useCompileWorkflowCanvasEphemeral() {
  return useMutation({
    mutationFn: (body: WorkflowCanvasUpsert) => compileWorkflowCanvasEphemeral(getTenantId(), body),
  });
}
