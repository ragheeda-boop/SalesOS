function decodeJwtPayload(token: string): Record<string, unknown> | null {
  try {
    const parts = token.split(".");
    if (parts.length !== 3) return null;
    const payload = parts[1];
    const decoded = atob(payload.replace(/-/g, "+").replace(/_/g, "/"));
    return JSON.parse(decoded);
  } catch {
    return null;
  }
}

export function getTenantId(): string {
  if (typeof window !== "undefined") {
    const stored = localStorage.getItem("tenant_id");
    if (stored) return stored;
    const token = localStorage.getItem("access_token");
    if (token) {
      const payload = decodeJwtPayload(token);
      if (payload?.tenant_id) return String(payload.tenant_id);
    }
  }
  return "default";
}
