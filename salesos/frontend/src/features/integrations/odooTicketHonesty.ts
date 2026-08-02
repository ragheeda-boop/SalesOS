/** Tip STORY-09-04 Odoo SupportTicket honesty constants (mirror BE).
 * Not an invented HTTP API. Unlinked badge list still BE-blocked.
 * Not Production GO / RAG GO.
 */

/** Canonical SupportTicket stages from tip ticket_sync.py */
export const CANONICAL_TICKET_STAGES = [
  "new",
  "in_progress",
  "on_hold",
  "solved",
  "cancelled",
] as const;

/** Tip DEFAULT_ODOO_TICKET_STAGE_MAP (certify/CI). */
export const DEFAULT_ODOO_TICKET_STAGE_MAP: Record<string, string> = {
  "1": "new",
  "2": "in_progress",
  "3": "on_hold",
  "4": "solved",
  "5": "cancelled",
  new: "new",
  in_progress: "in_progress",
  on_hold: "on_hold",
  solved: "solved",
  cancelled: "cancelled",
  done: "solved",
  closed: "solved",
};

/** Tip DEFAULT_TICKET_MAPPINGS for Map step preset (helpdesk.ticket). */
export const DEFAULT_TICKET_MAPPINGS = [
  { external: "name", internal: "name", direction: "pull" },
  { external: "stage_id", internal: "stage", direction: "pull" },
  { external: "priority", internal: "priority", direction: "pull" },
  {
    external: "partner_id",
    internal: "partner_external_id",
    direction: "pull",
  },
] as const;

export function isTicketModel(model: string): boolean {
  return model.trim().toLowerCase() === "helpdesk.ticket";
}
