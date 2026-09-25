jest.useFakeTimers();

jest.mock("@/lib/api/client", () => ({
  __esModule: true,
  default: {
    get: jest.fn().mockResolvedValue({ data: { csrf_token: "test-csrf-token" } }),
    post: jest.fn().mockResolvedValue({}),
  },
}));

import { renderHook, act } from "@testing-library/react";
import apiClient from "@/lib/api/client";
import {
  track,
  useNbaExposureTracking,
  usePageTracking,
  useWidgetTracking,
} from "../analytics";

function parseRequestBody(callIndex = 0): {
  events: Array<{
    type: string;
    eventId: string;
    widgetId?: string;
    companyId?: string;
    metadata?: Record<string, unknown>;
  }>;
} {
  return (apiClient.post as jest.Mock).mock.calls[callIndex][1] as {
    events: Array<{
      type: string;
      eventId: string;
      widgetId?: string;
      companyId?: string;
      metadata?: Record<string, unknown>;
    }>;
  };
}

beforeEach(() => {
  jest.clearAllMocks();
  (apiClient.get as jest.Mock).mockResolvedValue({ data: { csrf_token: "test-csrf-token" } });
  (apiClient.post as jest.Mock).mockResolvedValue({});
  document.cookie = "csrf_token=; Max-Age=0; path=/";
});

describe("track", () => {
  it("sends authenticated batches on threshold with stable event IDs", () => {
    for (let i = 0; i < 50; i++) {
      track({ type: "widget.rendered", widgetId: `w-${i}` });
    }

    expect(apiClient.post).toHaveBeenCalledTimes(1);
    expect(apiClient.post).toHaveBeenCalledWith("/api/v1/analytics/events", expect.any(Object));
    const body = parseRequestBody(0);
    expect(body.events).toHaveLength(50);
    expect(body.events.every((event) => /^[0-9a-f-]{36}$/i.test(event.eventId))).toBe(true);
  });

  it("flushes on interval", () => {
    track({ type: "nba.viewed", metadata: { id: "1" } });
    expect(apiClient.post).not.toHaveBeenCalled();

    act(() => {
      jest.advanceTimersByTime(10_000);
    });

    expect(apiClient.post).toHaveBeenCalledTimes(1);
  });

  it("warms the CSRF cookie before telemetry may need page-exit delivery", () => {
    track({ type: "widget.rendered", widgetId: "widget-csrf-warmup" });

    expect(apiClient.get).toHaveBeenCalledWith("/api/v1/identity/csrf-token");
    window.dispatchEvent(new Event("pagehide"));
  });

  it("uses authenticated fetch keepalive for queued events on pagehide", () => {
    track({ type: "widget.rendered", widgetId: "widget-before-exit" });

    window.dispatchEvent(new Event("pagehide"));

    expect(apiClient.post).toHaveBeenCalledWith(
      "/api/v1/analytics/events",
      expect.objectContaining({ events: [expect.objectContaining({ widgetId: "widget-before-exit" })] }),
      { adapter: "fetch", fetchOptions: { keepalive: true } },
    );
  });

  it("retries in-flight events on pagehide with the same idempotency ID", async () => {
    let resolveInitial!: (value: unknown) => void;
    (apiClient.post as jest.Mock).mockImplementationOnce(
      () => new Promise((resolve) => { resolveInitial = resolve; }),
    );
    track({ type: "nba.accepted", companyId: "company-1", metadata: { actionId: "action-1" } });
    const originalEventId = parseRequestBody(0).events[0].eventId;

    window.dispatchEvent(new Event("pagehide"));

    expect(apiClient.post).toHaveBeenCalledTimes(2);
    expect(parseRequestBody(1).events[0].eventId).toBe(originalEventId);
    expect((apiClient.post as jest.Mock).mock.calls[1][2]).toEqual({
      adapter: "fetch",
      fetchOptions: { keepalive: true },
    });

    await act(async () => {
      resolveInitial({});
      await Promise.resolve();
    });
  });

  it("requeues failed sends for a later retry with the same idempotency ID", async () => {
    (apiClient.post as jest.Mock).mockRejectedValueOnce(new Error("temporary network failure"));
    track({ type: "widget.rendered", widgetId: "widget-retry" });
    act(() => {
      jest.advanceTimersByTime(10_000);
    });
    const originalEventId = parseRequestBody(0).events[0].eventId;
    await act(async () => {
      await Promise.resolve();
    });

    act(() => {
      jest.advanceTimersByTime(10_000);
    });

    expect(apiClient.post).toHaveBeenCalledTimes(2);
    expect(parseRequestBody(1).events[0].eventId).toBe(originalEventId);
  });

  it.each(["nba.accepted", "nba.rejected", "nba.executed", "nba.outcome_recorded"] as const)(
    "flushes %s immediately",
    (type) => {
      track({ type, companyId: "company-1", metadata: { actionId: "action-1" } });

      expect(apiClient.post).toHaveBeenCalledTimes(1);
      expect(parseRequestBody().events).toHaveLength(1);
      expect(parseRequestBody().events[0].type).toBe(type);
    },
  );
});

describe("usePageTracking", () => {
  it("tracks page on mount", () => {
    renderHook(() => usePageTracking("dashboard"));

    act(() => {
      jest.advanceTimersByTime(10_000);
    });

    expect(apiClient.post).toHaveBeenCalled();
    const body = parseRequestBody(0);
    expect(body.events[0].type).toBe("pilot.session_started");
    expect(body.events[0].metadata?.page).toBe("dashboard");
  });
});

describe("useWidgetTracking", () => {
  it("tracks widget rendered on mount", () => {
    renderHook(() => useWidgetTracking("widget-1"));

    act(() => {
      jest.advanceTimersByTime(10_000);
    });

    expect(apiClient.post).toHaveBeenCalled();
    const body = parseRequestBody(0);
    expect(body.events[0].type).toBe("widget.rendered");
    expect(body.events[0].widgetId).toBe("widget-1");
  });

  it("returns interact function that tracks interaction", () => {
    const { result } = renderHook(() => useWidgetTracking("widget-1"));

    act(() => {
      result.current.interact("click", { target: "button" });
    });
    act(() => {
      jest.advanceTimersByTime(10_000);
    });

    expect(apiClient.post).toHaveBeenCalled();
    const body = parseRequestBody(0);
    const event = body.events.find((e) => e.type === "widget.interacted");
    expect(event).toBeDefined();
    expect(event?.widgetId).toBe("widget-1");
    expect(event?.metadata?.action).toBe("click");
  });

  it("only tracks rendered once even with widgetId change", async () => {
    const { rerender } = renderHook((id: string) => useWidgetTracking(id), {
      initialProps: "widget-1",
    });
    rerender("widget-2");

    act(() => {
      jest.advanceTimersByTime(10_000);
    });

    const body = parseRequestBody(0);
    const rendered = body.events.filter((e) => e.type === "widget.rendered");
    expect(rendered.length).toBe(1);
  });
});

describe("useNbaExposureTracking", () => {
  it("records each recommendation exposure once per company", () => {
    const initial = [{ id: "nba-1", action: "call" }];
    const { rerender } = renderHook(
      ({ recommendations, enabled }) =>
        useNbaExposureTracking("company-1", recommendations, enabled),
      { initialProps: { recommendations: initial, enabled: false } },
    );
    rerender({ recommendations: [...initial], enabled: true });
    rerender({ recommendations: [...initial], enabled: true });

    act(() => {
      jest.advanceTimersByTime(10_000);
    });

    const events = parseRequestBody(0).events;
    expect(events).toHaveLength(1);
    expect(events[0].type).toBe("nba.viewed");
    expect(events[0].companyId).toBe("company-1");
    expect(events[0].metadata?.recommendationId).toBe("nba-1");
  });
});
