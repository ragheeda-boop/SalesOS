/** Tip STORY-11-05 Enrichment Waterfall honesty (mirror BE crumb).
 * ≥2 in-memory FakeEnrichment providers. Live Clearbit/Apollo/ERP not claimed.
 * Not Production GO / RAG GO.
 */

export const ENRICHMENT_HONESTY =
  "Tip POST/GET /api/v1/gtm/enrichment (+ /meta). Waterfall first non-empty value wins (≥2 swappable providers; CI: fake_a/fake_b). Live Clearbit/Apollo/ERP enrichment not claimed.";

export const ENRICHMENT_NON_GOALS = [
  "Live Clearbit / Apollo / vendor network calls",
  "Live ERP enrichment pull",
  "Lookalike ML (STORY-11-04)",
  "Postgres enrichment persistence / Alembic",
  "Live 141221 Postgres",
] as const;
