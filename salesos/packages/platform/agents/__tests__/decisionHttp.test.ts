import type {
  DecisionContext,
  DecisionResult,
} from "@salesos/decision-platform";
import {
  configureDecisionHttp,
  evaluateDecision,
  setDecisionEvaluate,
} from "../decisionHttp";

const context: DecisionContext = {
  tenantId: "tenant-1",
  actorId: "agent-1",
  entityId: "company-1",
  entityType: "company",
};

const result = {
  decisionId: "decision-1",
  context,
  recommendation: {
    action: "proceed",
    actionLabel: "Proceed",
    confidence: 0.9,
  },
  scores: [],
  rulesApplied: [],
  evidence: [],
  explainability: { summary: "ok", factors: [] },
  telemetry: {
    evaluationTimeMs: 1,
    rulesTimeMs: 0,
    scoringTimeMs: 0,
    evidenceTimeMs: 0,
    recommendationTimeMs: 0,
  },
  timestamp: "2026-09-29T00:00:00.000Z",
} as unknown as DecisionResult;

afterEach(() => {
  setDecisionEvaluate(null);
  configureDecisionHttp(null);
});

describe("decision HTTP adapter", () => {
  it("uses the injected evaluator for orchestration tests", async () => {
    setDecisionEvaluate(async (received) => {
      expect(received).toEqual(context);
      return result;
    });

    await expect(evaluateDecision(context)).resolves.toBe(result);
  });

  it("posts the tenant-scoped context to the configured evaluation endpoint", async () => {
    const fetcher = jest.fn().mockResolvedValue({
      ok: true,
      status: 200,
      statusText: "OK",
      json: async () => result,
    });
    configureDecisionHttp({
      baseUrl: "http://decision-center.local/",
      bearerToken: "token-1",
      fetcher,
    });

    await expect(evaluateDecision(context)).resolves.toBe(result);
    expect(fetcher).toHaveBeenCalledWith(
      "http://decision-center.local/api/v1/decision/evaluate",
      expect.objectContaining({
        method: "POST",
        headers: expect.objectContaining({
          Authorization: "Bearer token-1",
          "X-Tenant-Id": "tenant-1",
        }),
        body: JSON.stringify(context),
      }),
    );
  });

  it("fails closed when no evaluator or HTTP client is configured", async () => {
    await expect(evaluateDecision(context)).rejects.toThrow("not configured");
  });

  it("surfaces non-success HTTP responses", async () => {
    configureDecisionHttp({
      baseUrl: "http://decision-center.local",
      fetcher: jest.fn().mockResolvedValue({
        ok: false,
        status: 503,
        statusText: "Service Unavailable",
        json: async () => ({}),
      }),
    });

    await expect(evaluateDecision(context)).rejects.toThrow(
      "Decision HTTP evaluation failed (503 Service Unavailable)",
    );
  });
});
