/** Tip STORY-10-04 Scoring Rules Studio honesty (mirror BE crumb).
 * In-memory MemScoringRulesStore — no Postgres / FORCE RLS claim.
 * Deterministic rules only (not LLM). Fail-safe → platform default on rule error.
 * Not Production GO / RAG GO.
 */

export const SCORING_RULES_HONESTY =
  "Tip POST/GET /api/v1/studio/scoring-rules + POST …/evaluate. Tenant dimension weights + attribute boosts override platform defaults; on rule error fail-safe falls back to platform default. Store is process-local in-memory — not Postgres. Deterministic only (not LLM).";

export const SCORING_RULES_NON_GOALS = [
  "Postgres persistence / Alembic scoring tables",
  "FORCE RLS / new POLICY_COUNT",
  "LLM / AI Studio scoring",
] as const;
