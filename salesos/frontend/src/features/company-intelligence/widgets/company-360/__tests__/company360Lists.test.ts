import { asDocumentRows, asTaskRows } from "../company360Lists";

describe("company360Lists (REMAINING_GAPS U04)", () => {
  it("maps activity-shaped documents", () => {
    const rows = asDocumentRows([
      {
        id: "d1",
        action: "document_uploaded",
        timestamp: "2026-07-05",
        metadata: { name: "اتفاقية", type: "PDF" },
      },
    ]);
    expect(rows).toEqual([
      { id: "d1", name: "اتفاقية", type: "PDF", date: "2026-07-05" },
    ]);
  });

  it("maps DTO-shaped documents and ignores empty payloads", () => {
    expect(asDocumentRows({ items: [{ id: "x", name: "شهادة", type: "PDF", date: "2026-01-10" }] })).toEqual([
      { id: "x", name: "شهادة", type: "PDF", date: "2026-01-10" },
    ]);
    expect(asDocumentRows(null)).toEqual([]);
    expect(asDocumentRows(undefined)).toEqual([]);
  });

  it("maps activity-shaped tasks for next-steps", () => {
    const rows = asTaskRows([
      {
        id: "t1",
        action: "task_created",
        timestamp: "2026-08-10",
        metadata: { title: "متابعة العرض", priority: "عاجل", status: "pending" },
      },
    ]);
    expect(rows[0]).toMatchObject({
      id: "t1",
      text: "متابعة العرض",
      priority: "عاجل",
      dueDate: "2026-08-10",
      status: "pending",
    });
  });

  it("returns empty next-steps when tasks are missing", () => {
    expect(asTaskRows([])).toEqual([]);
  });
});
