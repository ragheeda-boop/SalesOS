/** Tip STORY-09-05 Odoo Task + TaskCaseExtension honesty (mirror BE).
 * Not an invented HTTP API. Unlinked badge list still BE-blocked.
 * Not Production GO / RAG GO.
 */

/** Tip DEFAULT_TASK_MAPPINGS for Map step preset (project.task). */
export const DEFAULT_TASK_MAPPINGS = [
  { external: "name", internal: "name", direction: "pull" },
  { external: "stage_id", internal: "stage", direction: "pull" },
] as const;

/** Soft stage map (tip DEFAULT_TASK_STAGE_MAP) — not strict ACL. */
export const DEFAULT_TASK_STAGE_MAP: Record<string, string> = {
  "1": "new",
  "2": "in_progress",
  "3": "done",
  new: "new",
  in_progress: "in_progress",
  done: "done",
};

/** Tip CASE_TYPES — VO case_type literals (no independent aggregate id). */
export const TASK_CASE_TYPES = ["financing", "insurance", "generic"] as const;

/** Tip FINANCING_FIELDS / INSURANCE_FIELDS (classify only; not secrets). */
export const TASK_FINANCING_FIELDS = [
  "x_studio_financing_amount_requested",
  "x_studio_approved_financing_amount",
  "x_studio_unified_agreement_status",
] as const;

export const TASK_INSURANCE_FIELDS = [
  "x_studio_coverage_value",
  "x_studio_policy_provider",
] as const;

export function isTaskModel(model: string): boolean {
  return model.trim().toLowerCase() === "project.task";
}
