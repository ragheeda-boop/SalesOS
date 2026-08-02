/** Tip STORY-10-05 Territory Rules Studio honesty.
 * In-memory config over CAP-017 runtime. Live revenue DB / 141221 not claimed.
 * Not Production GO / RAG GO.
 */

export const TERRITORIES_STUDIO_HONESTY =
  "Tip GET/POST /api/v1/studio/territories (+ /meta, /assign, GET/DELETE /{id}). Geography / industry / size match conditions; unmatched does not invent a territory_key. Persistence=memory over CAP-017 runtime. Live revenue territory DB / 141221 not claimed.";

export const TERRITORIES_STUDIO_NON_GOALS = [
  "Postgres territory_rule_sets / new RLS",
  "Live CAP-017 revenue repository mutation",
  "Live 141221 Postgres",
  "Website Intelligence / AI Outreach (STORY-11-07/08)",
] as const;
