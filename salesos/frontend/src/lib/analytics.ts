"use client";

import { useEffect, useCallback, useRef } from "react";
import apiClient from "@/lib/api/client";
import {
  CSRF_COOKIE,
  CSRF_TOKEN_PATH,
  mirrorCsrfCookie,
  readCookie,
} from "@/lib/auth/csrf";

type EventType =
  | "widget.rendered"
  | "widget.interacted"
  | "nba.viewed"
  | "nba.accepted"
  | "nba.rejected"
  | "nba.executed"
  | "nba.outcome_recorded"
  | "opportunity.created"
  | "opportunity.stage_changed"
  | "search.performed"
  | "search.result_clicked"
  | "company.viewed"
  | "company.dna_viewed"
  | "pilot.feedback_submitted"
  | "pilot.session_started";

interface AnalyticsEvent {
  type: EventType;
  eventId: string;
  userId?: string;
  companyId?: string;
  widgetId?: string;
  metadata?: Record<string, unknown>;
  timestamp: string;
}

const queue: AnalyticsEvent[] = [];
const inFlight = new Map<string, AnalyticsEvent>();
const IMMEDIATE_EVENT_TYPES: ReadonlySet<EventType> = new Set([
  "nba.accepted",
  "nba.rejected",
  "nba.executed",
  "nba.outcome_recorded",
]);

function flush(options: { keepalive?: boolean } = {}) {
  if (typeof window === "undefined") return;
  const batch = options.keepalive
    ? Array.from(
        new Map(
          [...inFlight.values(), ...queue].map((event) => [event.eventId, event]),
        ).values(),
      ).slice(0, 50)
    : queue.splice(0, 50);
  if (batch.length === 0) return;
  const batchIds = new Set(batch.map((event) => event.eventId));
  if (options.keepalive) {
    for (let index = queue.length - 1; index >= 0; index--) {
      if (batchIds.has(queue[index].eventId)) queue.splice(index, 1);
    }
  }
  batch.forEach((event) => inFlight.set(event.eventId, event));

  // Keep the API client's request interceptors for Bearer, tenant, and CSRF
  // headers. The fetch adapter's keepalive lets a pagehide request outlive the
  // document; sendBeacon cannot carry the required authorization headers.
  const request = options.keepalive
    ? apiClient.post(
        "/api/v1/analytics/events",
        { events: batch },
        { adapter: "fetch", fetchOptions: { keepalive: true } },
      )
    : apiClient.post("/api/v1/analytics/events", { events: batch });
  void request.then(
    () => batch.forEach((event) => inFlight.delete(event.eventId)),
    () => {
      const queuedIds = new Set(queue.map((event) => event.eventId));
      batch.forEach((event) => {
        if (!queuedIds.has(event.eventId)) queue.push(event);
      });
    },
  );
}

let _interval: ReturnType<typeof setInterval> | null = null;
let _pagehideBound = false;
let _csrfWarmup: Promise<void> | null = null;

function warmCsrfCookie() {
  if (typeof window === "undefined" || readCookie(CSRF_COOKIE) || _csrfWarmup) return;

  _csrfWarmup = apiClient
    .get<{ csrf_token?: string }>(CSRF_TOKEN_PATH)
    .then((response) => {
      const token = String(response.data?.csrf_token || "");
      if (token && !readCookie(CSRF_COOKIE)) mirrorCsrfCookie(token);
    })
    .catch(() => {
      // Best-effort warmup; a later track() call may retry before page exit.
    })
    .finally(() => {
      _csrfWarmup = null;
    });
}

function ensureInterval() {
  if (_interval) clearInterval(_interval);
  _interval = setInterval(flush, 10_000);
  warmCsrfCookie();
  if (typeof window !== "undefined" && !_pagehideBound) {
    window.addEventListener("pagehide", () => flush({ keepalive: true }));
    _pagehideBound = true;
  }
}

export function track(event: Omit<AnalyticsEvent, "eventId" | "timestamp">) {
  ensureInterval();
  queue.push({
    ...event,
    eventId: crypto.randomUUID(),
    timestamp: new Date().toISOString(),
  });
  if (IMMEDIATE_EVENT_TYPES.has(event.type) || queue.length >= 50) flush();
}

export function usePageTracking(pageName: string) {
  useEffect(() => {
    track({ type: "pilot.session_started", metadata: { page: pageName } });
  }, [pageName]);
}

export function useWidgetTracking(widgetId: string) {
  const tracked = useRef(false);
  useEffect(() => {
    if (!tracked.current) {
      tracked.current = true;
      track({ type: "widget.rendered", widgetId });
    }
  }, [widgetId]);

  const interact = useCallback(
    (action: string, metadata?: Record<string, unknown>) => {
      track({
        type: "widget.interacted",
        widgetId,
        metadata: { action, ...metadata },
      });
    },
    [widgetId]
  );

  return { interact };
}

export function useNbaExposureTracking(
  companyId: string,
  recommendations: readonly { id?: string; action?: string }[],
  enabled = true,
) {
  const tracked = useRef(new Set<string>());

  useEffect(() => {
    if (!enabled) return;
    recommendations.forEach((recommendation) => {
      if (!recommendation.id) return;
      const exposureKey = `${companyId}:${recommendation.id}`;
      if (tracked.current.has(exposureKey)) return;

      tracked.current.add(exposureKey);
      track({
        type: "nba.viewed",
        companyId,
        metadata: {
          recommendationId: recommendation.id,
          actionType: recommendation.action,
        },
      });
    });
  }, [companyId, recommendations, enabled]);
}
