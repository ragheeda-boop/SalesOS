/**
 * Tenant Studio workflow canvas HTTP (STORY-10-03 / FE-S10-03).
 * Tip in-memory canvas → WorkflowEngine compile. No for_each / loops.
 * Not Production GO / RAG GO.
 */
import api from "./client";
import type {
  WorkflowCanvas,
  WorkflowCanvasCompileResult,
  WorkflowCanvasUpsert,
} from "./types/tenantStudio";

const BASE = "/api/v1/studio/workflows";

function tenantHeaders(tenantId: string) {
  return { "X-Tenant-Id": tenantId };
}

export async function listWorkflowCanvases(tenantId: string): Promise<WorkflowCanvas[]> {
  const resp = await api.get<WorkflowCanvas[]>(BASE, {
    headers: tenantHeaders(tenantId),
  });
  return resp.data;
}

export async function upsertWorkflowCanvas(
  tenantId: string,
  body: WorkflowCanvasUpsert
): Promise<WorkflowCanvas> {
  const resp = await api.post<WorkflowCanvas>(BASE, body, {
    headers: tenantHeaders(tenantId),
  });
  return resp.data;
}

export async function getWorkflowCanvas(
  tenantId: string,
  canvasId: string
): Promise<WorkflowCanvas> {
  const resp = await api.get<WorkflowCanvas>(`${BASE}/${canvasId}`, {
    headers: tenantHeaders(tenantId),
  });
  return resp.data;
}

export async function compileWorkflowCanvas(
  tenantId: string,
  canvasId: string
): Promise<WorkflowCanvasCompileResult> {
  const resp = await api.post<WorkflowCanvasCompileResult>(
    `${BASE}/${canvasId}/compile`,
    {},
    { headers: tenantHeaders(tenantId) }
  );
  return resp.data;
}

export async function compileWorkflowCanvasEphemeral(
  tenantId: string,
  body: WorkflowCanvasUpsert
): Promise<WorkflowCanvasCompileResult> {
  const resp = await api.post<WorkflowCanvasCompileResult>(`${BASE}/compile`, body, {
    headers: tenantHeaders(tenantId),
  });
  return resp.data;
}
