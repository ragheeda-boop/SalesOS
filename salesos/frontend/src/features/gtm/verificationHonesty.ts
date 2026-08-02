/** Tip STORY-11-06 Contact Verification honesty (mirror BE crumb).
 * Single VerificationConnector swap-in (CI: fake_verify).
 * Live NeverBounce/ZeroBounce/Twilio Lookup not claimed. Not Production GO / RAG GO.
 */

export const VERIFICATION_HONESTY =
  "Tip POST/GET /api/v1/gtm/verification (+ /meta). Single VerificationConnector commodity swap-in (CI: fake_verify). Live NeverBounce/ZeroBounce/Twilio Lookup not claimed.";

export const VERIFICATION_NON_GOALS = [
  "Live NeverBounce / ZeroBounce / Twilio Lookup",
  "LinkedIn channel (ToS risk)",
  "Lookalike ML (STORY-11-04)",
  "Postgres verification persistence / Alembic",
  "Live 141221 Postgres",
] as const;
