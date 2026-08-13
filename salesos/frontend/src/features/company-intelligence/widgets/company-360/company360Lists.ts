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
