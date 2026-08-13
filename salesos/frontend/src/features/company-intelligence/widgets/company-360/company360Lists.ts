import { asArray } from "@/lib/asArray";

export interface Company360DocumentRow {
  id: string;
  name: string;
  type: string;
  date: string;
}

export interface Company360TaskRow {
  id: string;
  text: string;
  priority: string;
  dueDate: string;
  status: string;
}

export interface Company360SettingsRow {
  id: string;
  label: string;
  value: string;
}

function asRecord(value: unknown): Record<string, unknown> {
  return value && typeof value === "object" ? (value as Record<string, unknown>) : {};
}

function str(value: unknown, fallback = ""): string {
  if (typeof value === "string" && value.trim()) return value;
  if (typeof value === "number" && Number.isFinite(value)) return String(value);
  return fallback;
}

function metaOf(item: Record<string, unknown>): Record<string, unknown> {
  return asRecord(item.metadata);
}

/** Map Company 360 `documents` (activity records or document DTOs) for the 360 panels. */
export function asDocumentRows(raw: unknown): Company360DocumentRow[] {
  return asArray<Record<string, unknown>>(raw).map((item, i) => {
    const rec = asRecord(item);
    const meta = metaOf(rec);
    return {
      id: str(rec.id, `doc-${i}`),
      name: str(rec.name || rec.title || meta.name || meta.title || rec.action, "—"),
      type: str(rec.type || meta.type || rec.action, "ملف"),
      date: str(rec.date || rec.timestamp || rec.created_at || meta.date),
    };
  });
}

/** Map Company 360 `tasks` (activity records or task DTOs) for next-steps. */
export function asTaskRows(raw: unknown): Company360TaskRow[] {
  return asArray<Record<string, unknown>>(raw).map((item, i) => {
    const rec = asRecord(item);
    const meta = metaOf(rec);
    return {
      id: str(rec.id, `task-${i}`),
      text: str(rec.text || rec.title || rec.name || meta.title || meta.text || rec.action, "—"),
      priority: str(rec.priority || meta.priority, "متوسط"),
      dueDate: str(rec.dueDate || rec.due_date || meta.due_date || rec.timestamp || rec.date),
      status: str(rec.status || meta.status),
    };
  });
}

function dateOnly(value: unknown): string {
  const raw = str(value);
  if (!raw) return "";
  return /^\d{4}-\d{2}-\d{2}/.test(raw) ? raw.slice(0, 10) : raw;
}

function joinNames(raw: unknown, keys: string[]): string {
  return asArray<Record<string, unknown>>(raw)
    .map((item) => {
      const rec = asRecord(item);
      for (const key of keys) {
        const v = str(rec[key]);
        if (v) return v;
      }
      return "";
    })
    .filter(Boolean)
    .join("، ");
}

function joinTags(raw: unknown): string {
  return asArray<unknown>(raw)
    .map((item) => (typeof item === "string" ? item.trim() : str(asRecord(item).name)))
    .filter(Boolean)
    .join("، ");
}

function pushRow(
  rows: Company360SettingsRow[],
  id: string,
  label: string,
  value: string
): void {
  if (value) rows.push({ id, label, value });
}

/**
 * Map Company 360 + company fields into a read-only settings/info panel.
 * There is no dedicated `settings` object on the API — omit missing fields; do not invent values.
 */
export function asSettingsRows(
  company360: unknown,
  companyFallback?: unknown
): Company360SettingsRow[] {
  const c360 = asRecord(company360);
  const company = { ...asRecord(companyFallback), ...asRecord(c360.company) };
  const org = asRecord(c360.organization);
  const enrichment = asRecord(c360.enrichment);
  const rows: Company360SettingsRow[] = [];

  pushRow(rows, "name_ar", "الاسم", str(company.name_ar || company.name));
  pushRow(rows, "name_en", "الاسم الإنجليزي", str(company.name_en));
  pushRow(rows, "cr_number", "السجل التجاري", str(company.cr_number));
  pushRow(rows, "status", "الحالة", str(company.status));
  pushRow(
    rows,
    "owner",
    "المالك",
    joinNames(c360.assigned_employees, ["full_name", "name", "email"])
  );
  pushRow(rows, "tags", "الوسوم", joinTags(company.tags));
  pushRow(rows, "city", "المدينة", str(company.city));
  pushRow(rows, "region", "المنطقة", str(company.region));
  pushRow(rows, "phone", "الهاتف", str(company.phone));
  pushRow(rows, "email", "البريد", str(company.email));
  pushRow(rows, "website", "الموقع", str(company.website));
  pushRow(
    rows,
    "legal_form",
    "الشكل القانوني",
    str(org.legal_form || company.legal_form)
  );
  pushRow(
    rows,
    "industry",
    "النشاط",
    str(company.industry || company.activity_description)
  );
  if (typeof company.employees_count === "number") {
    pushRow(rows, "employees_count", "عدد الموظفين", str(company.employees_count));
  } else if (typeof org.employees_count === "number" && org.employees_count > 0) {
    pushRow(rows, "employees_count", "عدد الموظفين", str(org.employees_count));
  }
  pushRow(
    rows,
    "incorporation_date",
    "تاريخ التأسيس",
    dateOnly(org.incorporation_date || company.incorporation_date)
  );
  if (typeof enrichment.is_golden_record === "boolean") {
    pushRow(rows, "golden_record", "سجل ذهبي", enrichment.is_golden_record ? "نعم" : "لا");
  }
  pushRow(rows, "created_at", "تاريخ الإنشاء", dateOnly(company.created_at));
  pushRow(rows, "updated_at", "آخر تحديث", dateOnly(company.updated_at));

  return rows;
}
