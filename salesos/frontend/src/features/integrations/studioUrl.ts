/** FE-S08-11 — Integrations Studio URL helpers. Not Production GO. */

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

export function buildStudioSearchParams(input: {
  step: StudioStepId;
  connectionId: string | null;
}): string {
  const params = new URLSearchParams();
  if (input.step && input.step !== "connect") {
    params.set("step", input.step);
  }
  if (input.connectionId) {
    params.set("connection", input.connectionId);
  }
  const qs = params.toString();
  return qs ? `?${qs}` : "";
}
