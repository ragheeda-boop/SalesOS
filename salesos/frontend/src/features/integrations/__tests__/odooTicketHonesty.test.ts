import {
  CANONICAL_TICKET_STAGES,
  DEFAULT_TICKET_MAPPINGS,
  isTicketModel,
} from "../odooTicketHonesty";

describe("odooTicketHonesty — FE-S09-04", () => {
  it("mirrors tip canonical ticket stages (no raw passthrough claim)", () => {
    expect(CANONICAL_TICKET_STAGES).toContain("solved");
    expect(CANONICAL_TICKET_STAGES).not.toContain("1");
  });

  it("provides tip helpdesk.ticket mapping preset including stage_id", () => {
    expect(isTicketModel("helpdesk.ticket")).toBe(true);
    expect(isTicketModel("mail.message")).toBe(false);
    expect(
      DEFAULT_TICKET_MAPPINGS.some(
        (m) => m.external === "stage_id" && m.internal === "stage",
      ),
    ).toBe(true);
  });
});
