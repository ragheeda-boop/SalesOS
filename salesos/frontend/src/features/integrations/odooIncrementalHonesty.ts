/** Tip STORY-09-07 Odoo incremental + feature flag honesty (mirror BE).
 * Tip SyncRunResponse includes cursor_before/after (STORY-09-09).
 * Not Production GO / RAG GO.
 */

/** Exact Grade-A admin_feature_flags key (tip FLAG_ODOO_INTEGRATION). */
export const FLAG_ODOO_INTEGRATION = "feature_odoo_integration" as const;

/** Design-partner slug from tip (real UUID resolved at ops — not invented). */
export const MUHIDE_TENANT_SLUG = "muhide" as const;

/** Hub paths gated when connector_key=odoo and flag evaluates off (tip 403). */
export const ODOO_FLAG_GATED_ACTIONS = ["connect", "test_connection", "schedule"] as const;

/** Tip cursor_state is a per-model watermark map on ConnectionResponse. */
export const CURSOR_STATE_HONESTY =
  "cursor_state holds per-model write_date watermarks (opaque strings)";

/** Tip SyncRunResponse cursor fields (STORY-09-09) — Monitor may display. */
export const SYNCRUN_CURSOR_HONESTY =
  "SyncRunResponse.cursor_before/after expose write_date watermarks on GET .../sync-runs";

export function isOdooConnectorKey(connectorKey: string): boolean {
  return connectorKey.trim().toLowerCase() === "odoo";
}
