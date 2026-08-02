/** Tip STORY-11-10 second-connector certification honesty.
 * HubSpot is CI Mem adapter. Live HubSpot network / pilot sync not claimed.
 * Not Production GO / RAG GO.
 */

export const SECOND_CONNECTOR_HONESTY =
  "Tip GET /api/v1/integrations/certify/meta + POST /api/v1/integrations/certify/{connector_key}. Identical certify_source_connector suite for fake / odoo / hubspot. HubSpot is in-memory CI; live HubSpot API / production pilot sync not claimed.";

export const SECOND_CONNECTOR_NON_GOALS = [
  "Live HubSpot OAuth / CRM network",
  "Production pilot tenant sync soak (R-02 residual OPEN)",
  "Territory Studio (STORY-10-05)",
  "Owner mint invent (DEC-093)",
] as const;
