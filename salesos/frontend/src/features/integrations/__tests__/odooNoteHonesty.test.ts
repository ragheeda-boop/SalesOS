import {
  DEFAULT_NOTE_MAPPINGS,
  NOTE_PII_SCRUB_CATEGORIES,
  isNoteModel,
} from "../odooNoteHonesty";

describe("odooNoteHonesty — FE-S09-03", () => {
  it("mirrors tip mail.message mappings including body", () => {
    expect(isNoteModel("mail.message")).toBe(true);
    expect(isNoteModel("crm.lead")).toBe(false);
    expect(
      DEFAULT_NOTE_MAPPINGS.some(
        (m) => m.external === "body" && m.internal === "body",
      ),
    ).toBe(true);
  });

  it("lists tip AI-GR-001 scrub categories without claiming RAG GO", () => {
    expect(NOTE_PII_SCRUB_CATEGORIES).toContain("email");
    expect(NOTE_PII_SCRUB_CATEGORIES).toContain("iban");
  });
});
