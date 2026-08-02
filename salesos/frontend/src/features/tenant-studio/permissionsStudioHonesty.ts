/** Tip STORY-10-06 Permissions Studio honesty (mirror BE crumb).
 * In-memory MemCustomRolesStore — no Postgres / FORCE RLS claim.
 * Custom roles capped at Plan.entitlements ceiling (EPIC-06). Owner plane blocked.
 * Not Production GO / RAG GO.
 */

export const PERMISSIONS_STUDIO_HONESTY =
  "Tip GET/PUT /api/v1/studio/permissions/{catalog,ceiling,check,roles}. Tenant-custom roles are capped at Plan.entitlements ceiling; privilege escalation returns 403. Store is process-local in-memory — not Postgres. Does not mutate Owner /admin/roles.";

export const PERMISSIONS_STUDIO_NON_GOALS = [
  "Postgres role persistence / Alembic",
  "FORCE RLS / new POLICY_COUNT",
  "Mutating Owner Admin /admin/roles",
] as const;
