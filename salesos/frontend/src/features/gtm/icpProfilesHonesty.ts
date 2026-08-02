/** Tip STORY-11-01 ICP Engine honesty (mirror BE crumb).
 * In-memory versioned ICPProfile + deterministic weighted fit.
 * No ML / won-lost backtest. Live 141221 not claimed. Not Production GO / RAG GO.
 */

export const ICP_PROFILES_HONESTY =
  "Tip POST/GET/PUT /api/v1/gtm/icp-profiles (+ /meta + /{id}/score). Versioned reusable ICPProfile in-memory — deterministic weighted fit only. No historical won/lost Opportunity backtest. Live 141,221 Postgres adapter not claimed.";

export const ICP_PROFILES_NON_GOALS = [
  "ML / Opportunity won-lost backtest",
  "Live prod SELECT of 141221 companies",
  "Postgres ICP persistence / Alembic",
  "Territory Studio (STORY-10-05)",
] as const;
