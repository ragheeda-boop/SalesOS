/** Tip STORY-09-03 Odoo InteractionNote honesty constants (mirror BE).
 * Not an invented HTTP API. Unlinked badge list still BE-blocked.
 * Not Production GO / RAG Production GO.
 */

/** Tip DEFAULT_NOTE_MAPPINGS for Map step preset (mail.message). */
export const DEFAULT_NOTE_MAPPINGS = [
  { external: "subject", internal: "subject", direction: "pull" },
  { external: "body", internal: "body", direction: "pull" },
] as const;

/** Tip optional mail.message externals (note_sync._OPTIONAL_NOTE_EXTERNALS). */
export const OPTIONAL_NOTE_EXTERNALS = [
  { internal: "message_type", external: "message_type" },
  { internal: "model", external: "model" },
  { internal: "res_id", external: "res_id" },
  { internal: "author_external_id", external: "author_id" },
  { internal: "date", external: "date" },
] as const;

/** AI-GR-001 scrub categories claimed by tip scrub_pii_for_rag (honesty only). */
export const NOTE_PII_SCRUB_CATEGORIES = [
  "phone",
  "email",
  "national_id",
  "iban",
  "card",
  "name",
] as const;

export function isNoteModel(model: string): boolean {
  return model.trim().toLowerCase() === "mail.message";
}
