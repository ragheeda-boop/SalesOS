/* eslint-disable @typescript-eslint/no-explicit-any */
import { deriveWidgets, deriveStatus } from "../widget.store";

describe("deriveStatus", () => {
  it("returns loading when isLoading and no data", () => {
    expect(deriveStatus(null, true, false)).toBe("loading");
  });

  it("returns degraded when isLoading and has data", () => {
    expect(deriveStatus({}, true, false)).toBe("degraded");
  });

  it("returns error when isError and no data", () => {
    expect(deriveStatus(null, false, true)).toBe("error");
  });

  it("returns degraded when isError and has data", () => {
    expect(deriveStatus({}, false, true)).toBe("degraded");
  });

  it("returns ready when no data and no loading/error", () => {
    // Absent/empty widgets are treated as ready (empty state), not loading.
    expect(deriveStatus(null, false, false)).toBe("ready");
  });

  it("returns ready when data is present", () => {
    expect(deriveStatus({}, false, false)).toBe("ready");
  });
});

describe("deriveWidgets", () => {
  it("returns all thirteen widgets with loading status", () => {
    const widgets = deriveWidgets(undefined, true, false);
    expect(Object.keys(widgets)).toEqual([
      "missionCenter",
      "decisionQueue",
      "intelligenceFeed",
      "aiBrief",
      "marketPulse",
      "recentActivity",
      "pipeline",
      "companyHealth",
      "companyEngagement",
      "emailIntelligence",
      "calendarIntelligence",
      "followupCenter",
      "companyScoring",
    ]);
    Object.values(widgets).forEach((w) => {
      expect(w.status).toBe("loading");
    });
  });

  it("returns mission center ready when dto present", () => {
    const dto: any = {
      missionCenter: {
        data: { companiesTracked: 100 },
        id: "mc",
        title: "MC",
        status: "ready",
        lastUpdated: null,
        actions: [],
      },
      decisionQueue: {
        data: { items: [], total: 0 },
        id: "dq",
        title: "DQ",
        status: "ready",
        lastUpdated: null,
        actions: [],
      },
      intelligenceFeed: {
        data: { items: [], total: 0, unseenCount: 0 },
        id: "if",
        title: "IF",
        status: "ready",
        lastUpdated: null,
        actions: [],
      },
      aiBrief: {
        data: { summary: "", highlights: [], generatedAt: "" },
        id: "ab",
        title: "AB",
        status: "ready",
        lastUpdated: null,
        actions: [],
      },
      marketPulse: {
        data: { trends: [], topMovers: [] },
        id: "mp",
        title: "MP",
        status: "ready",
        lastUpdated: null,
        actions: [],
      },
      recentActivity: {
        data: { items: [], total: 0 },
        id: "ra",
        title: "RA",
        status: "ready",
        lastUpdated: null,
        actions: [],
      },
      pipeline: {
        data: { opportunities: [], totalValue: 0 },
        id: "pl",
        title: "PL",
        status: "ready",
        lastUpdated: null,
        actions: [],
      },
      companyHealth: {
        data: { companies: [], averageScore: 0 },
        id: "ch",
        title: "CH",
        status: "ready",
        lastUpdated: null,
        actions: [],
      },
    };
    const widgets = deriveWidgets(dto, false, false);
    expect(widgets.missionCenter.status).toBe("ready");
    expect(widgets.missionCenter.data?.companiesTracked).toBe(100);
  });

  it("handles null dto gracefully", () => {
    const widgets = deriveWidgets(undefined, false, true);
    Object.values(widgets).forEach((w) => {
      expect(w.status).toBe("error");
    });
  });
});
