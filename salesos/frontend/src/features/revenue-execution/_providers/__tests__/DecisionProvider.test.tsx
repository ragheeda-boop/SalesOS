import { render, screen, renderHook, waitFor } from "@testing-library/react";
import type { ReactNode } from "react";

const mockPost = jest.fn();
const mockGet = jest.fn();

jest.mock("@/lib/api", () => ({
  __esModule: true,
  default: {
    post: (...args: unknown[]) => mockPost(...args),
    get: (...args: unknown[]) => mockGet(...args),
  },
}));

jest.mock("@/lib/hooks/useTenant", () => ({
  getTenantId: () => "tenant-1",
}));

const _mockScore = jest.fn();

jest.mock("@salesos/decision-platform", () => ({
  ScoringEngine: jest.fn(() => ({
    score: _mockScore,
  })),
}));

import { DecisionProvider, useDecision } from "../DecisionProvider";
import type { DecisionContext, DecisionResult } from "@salesos/decision-platform";

const sampleResult: DecisionResult = {
  id: "dec-1",
  recommendation: "follow_up",
  confidence: 0.85,
  action: "contact_decision_maker",
  reasoning: "ارتفاع نية الشراء",
  scores: [{ name: "buying_intent", value: 0.85, label: "نية الشراء", weight: 1 }],
  explainability: {
    factors: [
      {
        name: "signal",
        value: 0.9,
        description: "قوة الإشارة",
        impact: "high",
      },
    ],
    summary: "ملخص",
  },
};

const sampleContext: DecisionContext = {
  tenantId: "tenant-1",
  actorId: "actor-1",
  opportunityId: "opp-1",
  entityType: "opportunity",
};

function renderWithProvider(children: ReactNode) {
  return render(<DecisionProvider>{children}</DecisionProvider>);
}

describe("DecisionProvider", () => {
  beforeEach(() => {
    mockPost.mockReset();
    mockGet.mockReset();
    _mockScore.mockReset();
  });

  it("renders children", () => {
    renderWithProvider(<div data-testid="child">Hello</div>);
    expect(screen.getByTestId("child")).toHaveTextContent("Hello");
  });

  it("provides evaluate via Decision Platform API (not FE stub)", async () => {
    mockPost.mockResolvedValue({ data: sampleResult });

    const { result } = renderHook(() => useDecision(), {
      wrapper: DecisionProvider,
    });
    const output = await result.current.evaluate(sampleContext);

    expect(output).toEqual(sampleResult);
    expect(mockPost).toHaveBeenCalledWith(
      "/api/v1/decision/evaluate",
      expect.objectContaining({
        tenant_id: "tenant-1",
        actor_id: "actor-1",
        opportunity_id: "opp-1",
        entity_type: "opportunity",
      }),
      expect.any(Object)
    );
  });

  it("provides evaluateBatch via API", async () => {
    mockPost.mockResolvedValue({ data: { results: [sampleResult] } });

    const { result } = renderHook(() => useDecision(), {
      wrapper: DecisionProvider,
    });
    const output = await result.current.evaluateBatch([sampleContext]);

    expect(output).toEqual([sampleResult]);
    expect(mockPost).toHaveBeenCalledWith(
      "/api/v1/decision/batch",
      expect.any(Array),
      expect.any(Object)
    );
  });

  it("provides getRecommendation with correct context", async () => {
    mockPost.mockResolvedValue({ data: sampleResult });

    const { result } = renderHook(() => useDecision(), {
      wrapper: DecisionProvider,
    });
    const output = await result.current.getRecommendation("opp-1", "tenant-1", "actor-1");

    expect(output).toEqual(sampleResult);
    expect(mockPost).toHaveBeenCalledWith(
      "/api/v1/decision/evaluate",
      expect.objectContaining({
        tenant_id: "tenant-1",
        actor_id: "actor-1",
        opportunity_id: "opp-1",
      }),
      expect.any(Object)
    );
  });

  it("provides getScores extracting scores from result", async () => {
    mockPost.mockResolvedValue({ data: sampleResult });

    const { result } = renderHook(() => useDecision(), {
      wrapper: DecisionProvider,
    });
    const output = await result.current.getScores("entity-1", "opportunity", "tenant-1", "actor-1");

    expect(output).toEqual(sampleResult.scores);
  });

  it("provides getHistory via API", async () => {
    const historyItems = [
      {
        id: "hist-1",
        decisionId: "dec-1",
        action: "follow_up",
        outcome: "accepted",
        timestamp: "2026-07-10T10:00:00Z",
      },
    ];
    mockGet.mockResolvedValue({ data: { items: historyItems } });

    const { result } = renderHook(() => useDecision(), {
      wrapper: DecisionProvider,
    });
    const output = await result.current.getHistory("tenant-1", 10);

    expect(output).toEqual(historyItems);
    expect(mockGet).toHaveBeenCalledWith(
      "/api/v1/decision/history",
      expect.objectContaining({ params: { limit: 10 } })
    );
  });

  it("provides getExplainability via API", async () => {
    mockGet.mockResolvedValue({
      data: { explainability: sampleResult.explainability },
    });

    const { result } = renderHook(() => useDecision(), {
      wrapper: DecisionProvider,
    });
    const output = await result.current.getExplainability("dec-1");

    expect(output).toEqual(sampleResult.explainability);
    expect(mockGet).toHaveBeenCalledWith("/api/v1/decision/dec-1/explain", expect.any(Object));
  });

  it("provides submitFeedback via API", async () => {
    mockPost.mockResolvedValue({ data: { id: "fb-1", accepted: true } });

    const { result } = renderHook(() => useDecision(), {
      wrapper: DecisionProvider,
    });
    const feedback = {
      id: "fb-1",
      decisionId: "dec-1",
      outcome: "accepted" as const,
      revenueImpact: 50000,
      createdAt: "2026-07-10T10:00:00Z",
    };
    const output = await result.current.submitFeedback(feedback);

    expect(output).toEqual({ id: "fb-1", accepted: true });
    expect(mockPost).toHaveBeenCalledWith(
      "/api/v1/decision/feedback",
      expect.objectContaining({ decision_id: "dec-1", outcome: "accepted" }),
      expect.any(Object)
    );
  });

  it("provides getFeedbackStats via API", async () => {
    const stats = {
      total: 10,
      accepted: 7,
      rejected: 2,
      ignored: 1,
      acceptanceRate: 0.7,
      totalRevenueImpact: 350000,
      averageTimeToExecution: null,
    };
    mockGet.mockResolvedValue({ data: stats });

    const { result } = renderHook(() => useDecision(), {
      wrapper: DecisionProvider,
    });
    const output = await result.current.getFeedbackStats("tenant-1");

    expect(output).toEqual(stats);
  });

  it("provides score function (local ScoringEngine)", async () => {
    const scoreResult = {
      name: "custom",
      value: 0.75,
      label: "مخصص",
      weight: 1,
    };
    _mockScore.mockReturnValue(scoreResult);

    const { result } = renderHook(() => useDecision(), {
      wrapper: DecisionProvider,
    });
    const output = result.current.score(
      "buying_intent" as any,
      { signal: 0.8, engagement: 0.7 },
      { source: "test" }
    );

    expect(output).toEqual(scoreResult);
    expect(_mockScore).toHaveBeenCalledWith(
      "buying_intent",
      { signal: 0.8, engagement: 0.7 },
      { source: "test" }
    );
  });

  it("provides evaluate without tenant context", async () => {
    mockPost.mockResolvedValue({ data: sampleResult });

    const { result } = renderHook(() => useDecision(), {
      wrapper: DecisionProvider,
    });
    const ctx = { entityType: "company", actorId: "actor-1" };
    const output = await result.current.evaluate(ctx as any);

    expect(output).toEqual(sampleResult);
    await waitFor(() => {
      expect(mockPost).toHaveBeenCalled();
    });
  });
});

describe("useDecision outside provider", () => {
  it("throws error when used without DecisionProvider", () => {
    expect(() => renderHook(() => useDecision())).toThrow(
      "useDecision must be used within a DecisionProvider"
    );
  });
});
