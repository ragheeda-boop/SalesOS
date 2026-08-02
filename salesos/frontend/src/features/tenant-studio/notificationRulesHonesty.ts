/** Tip STORY-10-08 Notification Rules Studio honesty (mirror BE crumb).
 * In-memory MemNotificationRulesStore — no Postgres / FORCE RLS claim.
 * Compiles to existing rules_engine send_notification (no second interpreter).
 * Not Production GO / RAG GO.
 */

export const NOTIFICATION_RULES_HONESTY =
  "Tip GET/POST /api/v1/studio/notification-rules + …/route + …/compile. Tenant event→channel routing compiles to existing RulesEngine send_notification. Store is process-local in-memory — not Postgres.";

export const NOTIFICATION_RULES_NON_GOALS = [
  "Postgres rule persistence / Alembic",
  "FORCE RLS / new POLICY_COUNT",
  "Second notification interpreter",
] as const;
