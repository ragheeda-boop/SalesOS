/** Normalize list-or-envelope API payloads so `.map` / `.find` never throw. */
export function asArray<T = unknown>(value: unknown): T[] {
  if (Array.isArray(value)) return value as T[];
  if (value && typeof value === "object") {
    const rec = value as Record<string, unknown>;
    for (const key of ["items", "data", "results", "scores", "recommendations"] as const) {
      if (Array.isArray(rec[key])) return rec[key] as T[];
    }
  }
  return [];
}
