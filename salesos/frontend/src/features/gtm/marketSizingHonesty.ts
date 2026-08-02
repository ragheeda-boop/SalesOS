/** Tip STORY-11-02 Market Sizing honesty (mirror BE crumb).
 * CI gov-dataset-shaped in-memory universe — live 141221 Postgres adapter not claimed.
 * Not Production GO / RAG GO.
 */

export const MARKET_SIZING_HONESTY =
  "Tip POST/GET /api/v1/gtm/market-sizing (+ /meta + /{id}). TAM/SAM/SOM against gov-dataset-shaped in-memory universe — live 141,221 Postgres CompanyUniverse adapter not claimed. Invariant SOM ≤ SAM ≤ TAM ≤ universe_size.";

export const MARKET_SIZING_NON_GOALS = [
  "Live prod SELECT of 141221 companies",
  "ICP Engine (STORY-11-01)",
  "Lead Discovery (STORY-11-03)",
  "Postgres market-sizing persistence / Alembic",
] as const;
