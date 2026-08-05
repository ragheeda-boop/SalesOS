/** Custom Fields Studio honesty — process-local store; not production-persistent. */

export const CUSTOM_FIELDS_HONESTY =
  "Preview — Custom field definitions are stored in process memory for this studio — not Postgres. Definitions reset on process restart. Values/auto-render project into metadata.custom_fields only when wired; no durable ORM write yet.";

export const CUSTOM_FIELDS_AUTO_RENDER_HONESTY =
  "Form-schema returns Form Engine descriptors (renderer=custom_fields_auto). Value posts project metadata.custom_fields for known keys only — no ORM write / no Postgres persistence yet.";

export const CUSTOM_FIELDS_NON_GOALS = [
  "Postgres persistence / Alembic custom_* tables",
  "FORCE RLS / new POLICY_COUNT",
  "Hardcoded per-field React components",
] as const;
