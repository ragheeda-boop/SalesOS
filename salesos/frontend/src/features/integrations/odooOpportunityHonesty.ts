/** Tip STORY-09-02 Odoo opportunity honesty constants (mirror BE).
 * Not an invented HTTP API. Unlinked badge list still BE-blocked.
 * Not Production GO.
 */

/** Canonical SalesOS opportunity stages from tip opportunity_sync.py */
export const CANONICAL_OPPORTUNITY_STAGES = [
  "prospecting",
  "qualification",
  "proposal",
  "negotiation",
  "closed_won",
  "closed_lost",
] as const;

/** Certify/CI default Odoo→canonical map (tip DEFAULT_ODOO_OPPORTUNITY_STAGE_MAP). */
export const DEFAULT_ODOO_OPPORTUNITY_STAGE_MAP: Record<string, string> = {
  "1": "prospecting",
  "2": "qualification",
  "3": "proposal",
  "4": "negotiation",
  won: "closed_won",
  lost: "closed_lost",
  new: "prospecting",
  qualified: "qualification",
  proposition: "proposal",
};

/** Tip DEFAULT_OPPORTUNITY_MAPPINGS for Map step preset (crm.lead). */
export const DEFAULT_OPPORTUNITY_MAPPINGS = [
  { external: "name", internal: "name", direction: "pull" },
  { external: "stage_id", internal: "stage", direction: "pull" },
  { external: "expected_revenue", internal: "amount", direction: "pull" },
  {
    external: "partner_id",
    internal: "partner_external_id",
    direction: "pull",
  },
] as const;

export const HUB_MODEL_PRESETS = [
  // id avoids dots (Testing Library CSS testid selectors)
  {
    id: "res-partner",
    label: "res.partner (company/contact)",
    model: "res.partner",
  },
  { id: "crm-lead", label: "crm.lead (opportunity)", model: "crm.lead" },
  {
    id: "mail-message",
    label: "mail.message (InteractionNote)",
    model: "mail.message",
  },
] as const;

export function isOpportunityModel(model: string): boolean {
  return model.trim().toLowerCase() === "crm.lead";
}
