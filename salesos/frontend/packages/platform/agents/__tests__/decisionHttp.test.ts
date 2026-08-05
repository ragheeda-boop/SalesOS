import { evaluateDecision, setDecisionEvaluate } from "../decisionHttp";
import type { DecisionContext } from "@salesos/decision-platform";

describe("decisionHttp", () => {
  afterEach(() => {
    setDecisionEvaluate(null);
  });

  it("uses injected evaluator", async () => {
    const ctx: DecisionContext = {
      tenantId: "t1",
      actorId: "a1",
      entityType: "opportunity",
    };
    setDecisionEvaluate(async () => ({
      id: "inj",
      recommendation: { action: "x", confidence: 0.5 },
      confidence: 0.5,
      action: "x",
      reasoning: "injected",
      scores: [],
      evidence: [],
      explainability: { summary: "i", factors: [] },
    }));

    const result = await evaluateDecision(ctx);
    expect(result.id).toBe("inj");
  });

  it("HTTP default posts to Decision Center evaluate", async () => {
    const fetchMock = jest.fn().mockResolvedValue({
      ok: true,
      json: async () => ({
        id: "http-1",
        recommendation: { action: "y", confidence: 0.8 },
        confidence: 0.8,
        action: "y",
        reasoning: "http",
        scores: [],
        evidence: [],
        explainability: { summary: "h", factors: [] },
      }),
    });
    global.fetch = fetchMock as unknown as typeof fetch;

    setDecisionEvaluate(null);
    await evaluateDecision({
      tenantId: "tenant-abc",
      actorId: "user-1",
      entityType: "company",
      entityId: "c1",
    });

    expect(fetchMock).toHaveBeenCalledWith(
      "/api/v1/decision/evaluate",
      expect.objectContaining({
        method: "POST",
        credentials: "include",
      })
    );
    const init = fetchMock.mock.calls[0][1] as RequestInit;
    expect(init.headers).toMatchObject({
      "Content-Type": "application/json",
      "X-Tenant-Id": "tenant-abc",
    });
    expect(JSON.parse(String(init.body))).toMatchObject({
      tenant_id: "tenant-abc",
      actor_id: "user-1",
      entity_type: "company",
      entity_id: "c1",
    });
  });

  it("throws on non-OK Decision Center response", async () => {
    global.fetch = jest.fn().mockResolvedValue({
      ok: false,
      status: 503,
      text: async () => "unavailable",
    }) as unknown as typeof fetch;
    setDecisionEvaluate(null);

    await expect(
      evaluateDecision({
        actorId: "a1",
        entityType: "opportunity",
      })
    ).rejects.toThrow(/HTTP 503/);
  });
});
