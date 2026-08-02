/** Tip STORY-09-01 Odoo partner (company/contact) honesty constants (mirror BE).
 * Not an invented HTTP API. Unlinked badges on tip Monitor (FE-S09-08).
 * Not Production GO.
 */

/** Tip DEFAULT_PARTNER_MAPPINGS for Map step preset (res.partner). */
export const DEFAULT_PARTNER_MAPPINGS = [
  { external: "name", internal: "name", direction: "pull" },
  { external: "email", internal: "email", direction: "pull" },
  { external: "phone", internal: "phone", direction: "pull" },
  {
    external: "x_studio_cr_number",
    internal: "cr_number",
    direction: "pull",
  },
] as const;

/** Tip CrJoinResult.status values from cr_number_join.py (batch outcomes only). */
export const PARTNER_JOIN_OUTCOMES = [
  "matched",
  "unlinked",
  "invalid_cr",
] as const;

export function isPartnerModel(model: string): boolean {
  const key = model.trim().toLowerCase();
  return key === "res.partner" || key === "company" || key === "contact";
}
