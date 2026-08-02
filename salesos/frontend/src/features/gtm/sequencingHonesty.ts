/** Tip STORY-11-09 Sequencing honesty (mirror BE crumb).
 * Email-only in-memory state machine. Live SMTP / LinkedIn / WhatsApp not claimed.
 * Not Production GO / RAG GO.
 */

export const SEQUENCING_HONESTY =
  "Tip POST/GET /api/v1/gtm/sequences (+ enrollments / advance / pause / resume / cancel). Email-first SequenceDefinition + enrollment state machine with Task/Activity-shaped bindings (CI in-memory). Tip may advertise LinkedIn/WhatsApp partner channel shapes; this UI creates email steps only. Live SMTP / LinkedIn / WhatsApp network not claimed.";

export const SEQUENCING_NON_GOALS = [
  "Live SMTP / mailbox delivery",
  "Live LinkedIn / WhatsApp network sends",
  "ToS-risk LinkedIn browser automation",
  "Territory Studio (STORY-10-05)",
  "Live ML / 141221 Postgres",
  "Postgres sequence persistence / Alembic",
] as const;
