"use client";

import { useState } from "react";
import { Button, Input, Spinner, useToast } from "@salesos/ui";
import {
  useCompileNotificationRule,
  useNotificationEvents,
  useNotificationRules,
  useRouteNotificationEvent,
  useUpsertNotificationRule,
} from "@/lib/hooks/notificationRulesQueries";
import {
  NOTIFICATION_CHANNELS,
  NOTIFICATION_EVENT_TYPES,
} from "@/lib/api/types/tenantStudio";
import {
  NOTIFICATION_RULES_HONESTY,
  NOTIFICATION_RULES_NON_GOALS,
} from "@/features/tenant-studio/notificationRulesHonesty";

function getApiError(err: unknown): string {
  const detail = (err as { response?: { data?: { detail?: unknown } } })
    ?.response?.data?.detail;
  if (typeof detail === "string") return detail;
  if (err instanceof Error) return err.message;
  return "Request failed";
}

/**
 * FE-S10-08 — Notification Rules Studio against tip STORY-10-08 HTTP.
 * RulesEngine send_notification. Not Production GO / RAG GO. TenantList untouched.
 */
export function NotificationRulesStudio() {
  const { toast } = useToast();
  const eventsQuery = useNotificationEvents();
  const listQuery = useNotificationRules();
  const upsertMutation = useUpsertNotificationRule();
  const routeMutation = useRouteNotificationEvent();
  const compileMutation = useCompileNotificationRule();

  const [name, setName] = useState("Stage alert");
  const [eventType, setEventType] = useState<string>(
    NOTIFICATION_EVENT_TYPES[0],
  );
  const [channel, setChannel] = useState<string>(NOTIFICATION_CHANNELS[0]);
  const [recipientKind, setRecipientKind] = useState<"role" | "user" | "owner">(
    "role",
  );
  const [recipientValue, setRecipientValue] = useState("sales");
  const [messageTemplate, setMessageTemplate] = useState(
    "Opportunity stage changed",
  );
  const [routePayload, setRoutePayload] = useState('{\n  "stage": "won"\n}');

  const eventTypes = eventsQuery.data?.event_types?.length
    ? eventsQuery.data.event_types
    : [...NOTIFICATION_EVENT_TYPES];
  const channels = eventsQuery.data?.channels?.length
    ? eventsQuery.data.channels
    : [...NOTIFICATION_CHANNELS];

  return (
    <div className="space-y-4" data-testid="notification-rules-studio">
      <p
        className="rounded border border-amber-200 bg-amber-50 px-3 py-2 text-xs text-amber-950 dark:border-amber-800 dark:bg-amber-950/30 dark:text-amber-100"
        data-testid="notification-rules-honesty"
      >
        {NOTIFICATION_RULES_HONESTY} Non-goals:{" "}
        {NOTIFICATION_RULES_NON_GOALS.join("; ")}. Not Production GO / RAG GO.
      </p>

      <div className="flex flex-wrap items-center gap-3">
        <Button
          data-testid="notification-rules-refresh"
          disabled={listQuery.isFetching}
          onClick={() => {
            void listQuery.refetch();
            void eventsQuery.refetch();
          }}
        >
          Refresh
        </Button>
        <span
          className="text-sm text-[var(--text-muted)]"
          data-testid="notification-rules-count"
        >
          {listQuery.isLoading ? (
            <Spinner className="h-5 w-5" />
          ) : listQuery.isError ? (
            <span className="text-[var(--text-danger)]">
              {getApiError(listQuery.error)}
            </span>
          ) : (
            <>{listQuery.data?.length ?? 0} rule(s)</>
          )}
        </span>
      </div>

      <ul
        className="divide-y divide-[var(--border-default)] rounded border border-[var(--border-default)]"
        data-testid="notification-rules-list"
      >
        {(listQuery.data ?? []).length === 0 ? (
          <li className="px-3 py-2 text-sm text-[var(--text-muted)]">
            No notification rules yet. Upsert one below (tip POST).
          </li>
        ) : (
          (listQuery.data ?? []).map((rule) => (
            <li
              key={rule.id}
              className="flex flex-wrap items-center justify-between gap-2 px-3 py-2 text-sm"
              data-testid="notification-rules-row"
            >
              <span>
                <span className="font-medium">{rule.name}</span> ·{" "}
                {rule.event_type} · {rule.channels.join(",")}
                <span className="mt-0.5 block font-mono text-xs text-[var(--text-muted)]">
                  {rule.id}
                </span>
              </span>
              <Button
                data-testid={`notification-compile-${rule.id}`}
                disabled={compileMutation.isPending}
                onClick={() => {
                  compileMutation.mutate(rule.id, {
                    onSuccess: () => {
                      toast({
                        variant: "success",
                        title: "Compiled to RulesEngine",
                        description: rule.id,
                      });
                    },
                    onError: (err) => {
                      toast({
                        variant: "error",
                        title: "Compile failed",
                        description: getApiError(err),
                      });
                    },
                  });
                }}
              >
                Compile
              </Button>
            </li>
          ))
        )}
      </ul>

      <form
        className="space-y-3 rounded border border-[var(--border-default)] p-3"
        data-testid="notification-rules-upsert-form"
        onSubmit={(e) => {
          e.preventDefault();
          upsertMutation.mutate(
            {
              name: name.trim(),
              event_type: eventType,
              channels: [channel],
              recipients: [
                { kind: recipientKind, value: recipientValue.trim() },
              ],
              message_template: messageTemplate,
              active: true,
            },
            {
              onSuccess: (row) => {
                toast({
                  variant: "success",
                  title: "Notification rule saved",
                  description: `${row.name} (${row.id})`,
                });
              },
              onError: (err) => {
                toast({
                  variant: "error",
                  title: "Upsert failed",
                  description: getApiError(err),
                });
              },
            },
          );
        }}
      >
        <h2 className="text-sm font-semibold text-[var(--text-primary)]">
          Upsert rule (tip POST)
        </h2>
        <Input
          label="name"
          data-testid="notification-rules-name"
          value={name}
          onChange={(e) => setName(e.target.value)}
        />
        <div>
          <label className="block text-xs text-[var(--text-muted)]">
            event_type
          </label>
          <select
            data-testid="notification-rules-event-type"
            className="w-full max-w-md rounded border border-[var(--border-default)] bg-[var(--bg-primary)] px-3 py-2 text-sm"
            value={eventType}
            onChange={(e) => setEventType(e.target.value)}
          >
            {eventTypes.map((et) => (
              <option key={et} value={et}>
                {et}
              </option>
            ))}
          </select>
        </div>
        <div>
          <label className="block text-xs text-[var(--text-muted)]">
            channel
          </label>
          <select
            data-testid="notification-rules-channel"
            className="w-full max-w-xs rounded border border-[var(--border-default)] bg-[var(--bg-primary)] px-3 py-2 text-sm"
            value={channel}
            onChange={(e) => setChannel(e.target.value)}
          >
            {channels.map((ch) => (
              <option key={ch} value={ch}>
                {ch}
              </option>
            ))}
          </select>
        </div>
        <div className="grid gap-2 sm:grid-cols-2">
          <div>
            <label className="block text-xs text-[var(--text-muted)]">
              recipient.kind
            </label>
            <select
              data-testid="notification-rules-recipient-kind"
              className="w-full rounded border border-[var(--border-default)] bg-[var(--bg-primary)] px-3 py-2 text-sm"
              value={recipientKind}
              onChange={(e) =>
                setRecipientKind(e.target.value as "role" | "user" | "owner")
              }
            >
              <option value="role">role</option>
              <option value="user">user</option>
              <option value="owner">owner</option>
            </select>
          </div>
          <Input
            label="recipient.value"
            data-testid="notification-rules-recipient-value"
            value={recipientValue}
            onChange={(e) => setRecipientValue(e.target.value)}
          />
        </div>
        <Input
          label="message_template"
          data-testid="notification-rules-message"
          value={messageTemplate}
          onChange={(e) => setMessageTemplate(e.target.value)}
        />
        <Button
          type="submit"
          data-testid="notification-rules-submit"
          disabled={upsertMutation.isPending || !name.trim()}
        >
          {upsertMutation.isPending ? "Saving…" : "Save notification rule"}
        </Button>
      </form>

      <form
        className="space-y-3 rounded border border-[var(--border-default)] p-3"
        data-testid="notification-rules-route-form"
        onSubmit={(e) => {
          e.preventDefault();
          let payload: Record<string, unknown> = {};
          try {
            payload = JSON.parse(routePayload) as Record<string, unknown>;
          } catch {
            toast({ variant: "error", title: "Invalid payload JSON" });
            return;
          }
          routeMutation.mutate(
            { event_type: eventType, payload, entity_id: "event" },
            {
              onSuccess: () => {
                toast({ variant: "success", title: "Routed event" });
              },
              onError: (err) => {
                toast({
                  variant: "error",
                  title: "Route failed",
                  description: getApiError(err),
                });
              },
            },
          );
        }}
      >
        <h2 className="text-sm font-semibold text-[var(--text-primary)]">
          Route event (tip POST …/route)
        </h2>
        <textarea
          data-testid="notification-rules-route-payload"
          className="min-h-[80px] w-full rounded border border-[var(--border-default)] bg-[var(--bg-primary)] p-2 font-mono text-xs"
          value={routePayload}
          onChange={(e) => setRoutePayload(e.target.value)}
        />
        <Button
          type="submit"
          data-testid="notification-rules-route"
          disabled={routeMutation.isPending}
        >
          {routeMutation.isPending ? "Routing…" : "Route event"}
        </Button>
        {routeMutation.data || compileMutation.data ? (
          <pre
            className="overflow-auto rounded border border-[var(--border-default)] bg-[var(--bg-primary)] p-2 font-mono text-[10px] text-[var(--text-muted)]"
            data-testid="notification-rules-result"
          >
            {JSON.stringify(
              routeMutation.data || compileMutation.data,
              null,
              2,
            )}
          </pre>
        ) : null}
      </form>
    </div>
  );
}
