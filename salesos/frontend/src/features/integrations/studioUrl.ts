/** FE-S08-11/12 — Integrations Studio URL helpers. Not Production GO. */

import { STUDIO_STEPS } from "@/features/admin/IntegrationsStudioShell";

export type StudioStepId = (typeof STUDIO_STEPS)[number]["id"];

const STEP_IDS = new Set<string>(STUDIO_STEPS.map((s) => s.id));

export function parseStudioStep(
  raw: string | null | undefined,
): StudioStepId | null {
  if (!raw) return null;
  const value = raw.trim().toLowerCase();
  return STEP_IDS.has(value) ? (value as StudioStepId) : null;
}

/** Client-side SyncRun status filter (tip SyncRun.status values). */
export function parseRunStatusFilter(raw: string | null | undefined): string {
  if (!raw) return "all";
  const value = raw.trim().toLowerCase();
  if (!value) return "all";
  return value;
}

/** Client-side SyncRun model filter (tip SyncRun.model). */
export function parseRunModelFilter(raw: string | null | undefined): string {
  if (!raw) return "all";
  const value = raw.trim();
  if (!value || value.toLowerCase() === "all") return "all";
  return value;
}

export function buildStudioSearchParams(input: {
  step: StudioStepId;
  connectionId: string | null;
  runStatus?: string;
  runModel?: string;
}): string {
  const params = new URLSearchParams();
  if (input.step && input.step !== "connect") {
    params.set("step", input.step);
  }
  if (input.connectionId) {
    params.set("connection", input.connectionId);
  }
  if (input.step === "monitor") {
    const status = (input.runStatus || "all").trim().toLowerCase() || "all";
    if (status !== "all") params.set("runStatus", status);
    const model = (input.runModel || "all").trim() || "all";
    if (model.toLowerCase() !== "all") params.set("runModel", model);
  }
  const qs = params.toString();
  return qs ? `?${qs}` : "";
}
