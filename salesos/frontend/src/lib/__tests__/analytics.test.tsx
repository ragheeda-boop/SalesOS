jest.useFakeTimers();

import { renderHook, act } from "@testing-library/react";
import { track, usePageTracking, useWidgetTracking } from "../analytics";

/** Production flush() sends a Blob; older tests assumed a JSON string. */
async function blobToText(blob: Blob): Promise<string> {
  if (typeof blob.text === "function") {
    return blob.text();
  }
  // jsdom Blobs often lack Blob.text() — FileReader is the portable path.
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(String(reader.result ?? ""));
    reader.onerror = () => reject(reader.error);
    reader.readAsText(blob);
  });
}

async function parseBeaconBody(callIndex = 0): Promise<{
  events: Array<{
    type: string;
    widgetId?: string;
    metadata?: Record<string, unknown>;
  }>;
}> {
  const payload = (navigator.sendBeacon as jest.Mock).mock.calls[callIndex][1];
  if (payload instanceof Blob) {
    return JSON.parse(await blobToText(payload));
  }
  return JSON.parse(payload as string);
}

beforeEach(() => {
  jest.clearAllMocks();
  Object.defineProperty(navigator, "sendBeacon", {
    value: jest.fn().mockReturnValue(true),
    configurable: true,
    writable: true,
  });
});

describe("track", () => {
  it("queues events and flushes on threshold", async () => {
    for (let i = 0; i < 50; i++) {
      track({ type: "widget.rendered", widgetId: `w-${i}` });
    }

    expect(navigator.sendBeacon).toHaveBeenCalledTimes(1);
    const body = await parseBeaconBody(0);
    expect(body.events).toHaveLength(50);
  });

  it("flushes on interval", () => {
    track({ type: "nba.viewed", metadata: { id: "1" } });
    expect(navigator.sendBeacon).not.toHaveBeenCalled();

    act(() => {
      jest.advanceTimersByTime(10_000);
    });

    expect(navigator.sendBeacon).toHaveBeenCalledTimes(1);
  });
});

describe("usePageTracking", () => {
  it("tracks page on mount", async () => {
    renderHook(() => usePageTracking("dashboard"));

    act(() => {
      jest.advanceTimersByTime(10_000);
    });

    expect(navigator.sendBeacon).toHaveBeenCalled();
    const body = await parseBeaconBody(0);
    expect(body.events[0].type).toBe("pilot.session_started");
    expect(body.events[0].metadata?.page).toBe("dashboard");
  });
});

describe("useWidgetTracking", () => {
  it("tracks widget rendered on mount", async () => {
    renderHook(() => useWidgetTracking("widget-1"));

    act(() => {
      jest.advanceTimersByTime(10_000);
    });

    expect(navigator.sendBeacon).toHaveBeenCalled();
    const body = await parseBeaconBody(0);
    expect(body.events[0].type).toBe("widget.rendered");
    expect(body.events[0].widgetId).toBe("widget-1");
  });

  it("returns interact function that tracks interaction", async () => {
    const { result } = renderHook(() => useWidgetTracking("widget-1"));

    act(() => {
      result.current.interact("click", { target: "button" });
    });
    act(() => {
      jest.advanceTimersByTime(10_000);
    });

    expect(navigator.sendBeacon).toHaveBeenCalled();
    const body = await parseBeaconBody(0);
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

    const body = await parseBeaconBody(0);
    const rendered = body.events.filter((e) => e.type === "widget.rendered");
    expect(rendered.length).toBe(1);
  });
});
