import { asDocumentRows, asSettingsRows, asTaskRows } from "../company360Lists";

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

describe("company360Lists settings (360 settings panel)", () => {
  it("maps existing company360 fields and omits missing ones", () => {
    const rows = asSettingsRows({
      company: {
        name_ar: "شركة الاختبار",
        name_en: "Test Co",
        cr_number: "1010",
        status: "active",
        tags: ["vip", "ksa"],
        city: "الرياض",
        website: "https://example.test",
      },
      assigned_employees: [{ id: "u-1", full_name: "أحمد" }],
      organization: { legal_form: "ذات مسؤولية محدودة", employees_count: 12 },
      enrichment: { is_golden_record: false },
    });
    expect(rows).toEqual(
      expect.arrayContaining([
        { id: "name_ar", label: "الاسم", value: "شركة الاختبار" },
        { id: "name_en", label: "الاسم الإنجليزي", value: "Test Co" },
        { id: "cr_number", label: "السجل التجاري", value: "1010" },
        { id: "status", label: "الحالة", value: "active" },
        { id: "owner", label: "المالك", value: "أحمد" },
        { id: "tags", label: "الوسوم", value: "vip، ksa" },
        { id: "city", label: "المدينة", value: "الرياض" },
        { id: "website", label: "الموقع", value: "https://example.test" },
        { id: "legal_form", label: "الشكل القانوني", value: "ذات مسؤولية محدودة" },
        { id: "employees_count", label: "عدد الموظفين", value: "12" },
        { id: "golden_record", label: "سجل ذهبي", value: "لا" },
      ])
    );
    expect(rows.find((r) => r.id === "phone")).toBeUndefined();
    expect(rows.find((r) => r.id === "email")).toBeUndefined();
  });

  it("falls back to company detail when 360 has no nested company", () => {
    const rows = asSettingsRows({}, { name_ar: "من التفاصيل", status: "inactive" });
    expect(rows).toEqual([
      { id: "name_ar", label: "الاسم", value: "من التفاصيل" },
      { id: "status", label: "الحالة", value: "inactive" },
    ]);
  });

  it("returns empty when no company fields exist (no fake sample data)", () => {
    expect(asSettingsRows(null)).toEqual([]);
    expect(asSettingsRows(undefined, undefined)).toEqual([]);
    expect(asSettingsRows({ assigned_employees: [], organization: {} })).toEqual([]);
  });
});
