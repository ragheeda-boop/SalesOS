/** Tip STORY-10-03 Workflow Builder honesty (mirror BE crumb).
 * In-memory MemWorkflowCanvasStore — no Postgres / FORCE RLS claim.
 * Compiles to existing WorkflowEngine (no second interpreter). for_each deferred.
 * Not Production GO / RAG GO.
 */

export const WORKFLOW_STUDIO_HONESTY =
  "Tip POST/GET /api/v1/studio/workflows + …/compile. Canvas compiles to existing WorkflowEngine (no second interpreter). Store is process-local in-memory — not Postgres. for_each / loop canvas nodes deferred (Sprint-13 debt).";

export const WORKFLOW_STUDIO_NON_GOALS = [
  "Postgres canvas persistence / Alembic",
  "FORCE RLS / new POLICY_COUNT",
  "for_each / loop canvas nodes",
] as const;
