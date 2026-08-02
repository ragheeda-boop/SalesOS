/** Tip STORY-10-01/10-02 Tenant Studio honesty (mirror BE crumbs).
 * In-memory store — no Postgres / FORCE RLS claim.
 * Not Production GO / RAG GO.
 */

export const CUSTOM_FIELDS_HONESTY =
  "Tip POST/GET /api/v1/studio/custom-fields defines versioned scalar fields (string|number|date|enum) with reserved-column collision checks. Store is process-local in-memory — not Postgres. Values and page auto-render are STORY-10-02.";

export const CUSTOM_FIELDS_AUTO_RENDER_HONESTY =
  "Tip GET .../form-schema returns Form Engine descriptors (renderer=custom_fields_auto). POST .../values projects metadata.custom_fields for known keys only — no ORM write / no Postgres persistence on tip.";

export const CUSTOM_FIELDS_NON_GOALS = [
  "Postgres persistence / Alembic custom_* tables",
  "FORCE RLS / new POLICY_COUNT",
  "Hardcoded per-field React components",
] as const;
