/** Tip STORY-09-07 Odoo incremental + feature flag honesty (mirror BE).
 * Not an invented HTTP API. Unlinked badge list still BE-blocked.
 * Not Production GO / RAG GO.
 */

/** Exact Grade-A admin_feature_flags key (tip FLAG_ODOO_INTEGRATION). */
export const FLAG_ODOO_INTEGRATION = "feature_odoo_integration" as const;

/** Design-partner slug from tip (real UUID resolved at ops — not invented). */
export const MUHIDE_TENANT_SLUG = "muhide" as const;

/** Hub paths gated when connector_key=odoo and flag evaluates off (tip 403). */
export const ODOO_FLAG_GATED_ACTIONS = [
  "connect",
  "test_connection",
  "schedule",
] as const;

/**
 * Tip cursor_state is a per-model watermark map on ConnectionResponse.
 * SyncRun cursor_before/after exist on ORM but are NOT on SyncRunResponse —
 * do not invent Monitor fields.
 */
export const CURSOR_STATE_HONESTY =
  "cursor_state holds per-model write_date watermarks (opaque strings)";

export function isOdooConnectorKey(connectorKey: string): boolean {
  return connectorKey.trim().toLowerCase() === "odoo";
}
