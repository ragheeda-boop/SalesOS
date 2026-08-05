/**
 * Tenant Studio notification-rules HTTP (STORY-10-08 / FE-S10-08).
 * Tip in-memory rules → RulesEngine send_notification. Not Production GO / RAG GO.
 */
import api from "./client";
import type {
  NotificationEventsCatalog,
  NotificationRouteRequest,
  NotificationRouteResult,
  NotificationRule,
  NotificationRuleCompileResult,
  NotificationRuleUpsert,
} from "./types/tenantStudio";

const BASE = "/api/v1/studio/notification-rules";

function tenantHeaders(tenantId: string) {
  return { "X-Tenant-Id": tenantId };
}

export async function listNotificationEvents(tenantId: string): Promise<NotificationEventsCatalog> {
  const resp = await api.get<NotificationEventsCatalog>(`${BASE}/events`, {
    headers: tenantHeaders(tenantId),
  });
  return resp.data;
}

export async function listNotificationRules(tenantId: string): Promise<NotificationRule[]> {
  const resp = await api.get<NotificationRule[]>(BASE, {
    headers: tenantHeaders(tenantId),
  });
  return resp.data;
}

export async function upsertNotificationRule(
  tenantId: string,
  body: NotificationRuleUpsert
): Promise<NotificationRule> {
  const resp = await api.post<NotificationRule>(BASE, body, {
    headers: tenantHeaders(tenantId),
  });
  return resp.data;
}

export async function routeNotificationEvent(
  tenantId: string,
  body: NotificationRouteRequest
): Promise<NotificationRouteResult> {
  const resp = await api.post<NotificationRouteResult>(`${BASE}/route`, body, {
    headers: tenantHeaders(tenantId),
  });
  return resp.data;
}

export async function compileNotificationRule(
  tenantId: string,
  ruleId: string
): Promise<NotificationRuleCompileResult> {
  const resp = await api.post<NotificationRuleCompileResult>(
    `${BASE}/${ruleId}/compile`,
    {},
    { headers: tenantHeaders(tenantId) }
  );
  return resp.data;
}
