/** Tip STORY-10-07 Branding Studio honesty (mirror BE crumb).
 * In-memory MemBrandingStore — no Postgres / FORCE RLS claim.
 * Logo is URL string only (no CDN upload). Not Production GO / RAG GO.
 */

export const BRANDING_STUDIO_HONESTY =
  "Tip GET/PUT /api/v1/studio/branding. Display name, logo URL, colors, and locales are tenant-scoped in-memory — not Postgres. logo_url is https:// or /path only (no object upload / CDN). Dashboard chrome (FE-S10-07b) applies tip display_name + colors only.";

export const BRANDING_STUDIO_NON_GOALS = [
  "Object upload / CDN provisioning",
  "Postgres branding persistence / Alembic",
  "FORCE RLS / new POLICY_COUNT",
] as const;
