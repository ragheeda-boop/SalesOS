import { evaluateScoringRule, listScoringRules, upsertScoringRule } from "../scoringRules";

jest.mock("../client", () => ({
  __esModule: true,
  default: {
    get: jest.fn(),
    post: jest.fn(),
  },
}));

import api from "../client";

const mocked = api as unknown as {
  get: jest.Mock;
  post: jest.Mock;
};

describe("scoringRules API — FE-S10-04", () => {
  beforeEach(() => {
    mocked.get.mockReset();
    mocked.post.mockReset();
  });

  it("GETs tip scoring-rules list", async () => {
    mocked.get.mockResolvedValue({ data: [] });
    const rows = await listScoringRules("tenant-1");
    expect(mocked.get).toHaveBeenCalledWith(
      "/api/v1/studio/scoring-rules",
      expect.objectContaining({
        headers: { "X-Tenant-Id": "tenant-1" },
      })
    );
    expect(rows).toEqual([]);
  });

  it("POSTs tip scoring rule upsert", async () => {
    mocked.post.mockResolvedValue({
      data: {
        id: "r1",
        tenant_id: "t1",
        name: "Override",
        target_type: "lead",
        dimension_weights: { buying_intent: 1 },
        boosts: [],
        active: true,
        schema_version: 1,
      },
    });
    const row = await upsertScoringRule("tenant-1", {
      name: "Override",
      target_type: "lead",
      dimension_weights: { buying_intent: 1 },
    });
    expect(mocked.post).toHaveBeenCalledWith(
      "/api/v1/studio/scoring-rules",
      expect.objectContaining({ name: "Override" }),
      expect.objectContaining({
        headers: { "X-Tenant-Id": "tenant-1" },
      })
    );
    expect(row.id).toBe("r1");
  });

  it("POSTs tip scoring evaluate", async () => {
    mocked.post.mockResolvedValue({
      data: {
        score: 72.5,
        source: "tenant_rule",
        fallback_used: false,
        explanation: [],
        dimension_weights_used: { buying_intent: 1 },
      },
    });
    const result = await evaluateScoringRule("tenant-1", {
      target_type: "company",
      dimension_scores: { buying_intent: 80 },
      attributes: {},
    });
    expect(mocked.post).toHaveBeenCalledWith(
      "/api/v1/studio/scoring-rules/evaluate",
      expect.objectContaining({ target_type: "company" }),
      expect.objectContaining({
        headers: { "X-Tenant-Id": "tenant-1" },
      })
    );
    expect(result.score).toBe(72.5);
  });
});
