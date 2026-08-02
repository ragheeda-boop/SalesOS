/** Tip STORY-11-03 Lead Discovery honesty (mirror BE crumb).
 * Gov-first in-memory universe + FakeSourceConnector Hub fallback.
 * Live 141221 Postgres / live ERP not claimed. Not Production GO / RAG GO.
 */

export const LEAD_DISCOVERY_HONESTY =
  "Tip POST/GET /api/v1/gtm/lead-discovery (+ /meta). Government-data-first then Integration Hub provider fallback (CI: FakeSourceConnector). Live 141,221 Postgres / live ERP pull not claimed.";

export const LEAD_DISCOVERY_NON_GOALS = [
  "Live prod SELECT of 141221 companies",
  "Live Odoo/SAP/HubSpot pull",
  "ICP Engine (STORY-11-01)",
  "Postgres lead-discovery persistence / Alembic",
] as const;
