/** Tip STORY-10-01 custom field definition honesty (mirror BE crumb).
 * In-memory MemCustomFieldDefinitionService — no Postgres / FORCE RLS claim.
 * Auto-render on Company/Contact/Opportunity is STORY-10-02 (not this story).
 * Not Production GO / RAG GO.
 */

export const CUSTOM_FIELDS_HONESTY =
  "Tip POST/GET /api/v1/studio/custom-fields defines versioned scalar fields (string|number|date|enum) with reserved-column collision checks. Store is process-local in-memory — not Postgres. Values and page auto-render are STORY-10-02.";

export const CUSTOM_FIELDS_NON_GOALS = [
  "Postgres persistence / Alembic custom_* tables",
  "FORCE RLS / new POLICY_COUNT",
  "Value storage on Company/Contact/Opportunity",
  "Auto-render on entity pages (STORY-10-02)",
] as const;
