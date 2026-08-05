import {
  deleteAiPolicy,
  evaluateAiPolicy,
  getAiPoliciesMeta,
  getAiPolicy,
  listAiPolicies,
  upsertAiPolicy,
} from "../aiPoliciesStudio";

jest.mock("../client", () => ({
  __esModule: true,
  default: {
    get: jest.fn(),
    post: jest.fn(),
    delete: jest.fn(),
  },
}));

import api from "../client";

const mockedApi = api as unknown as {
  get: jest.Mock;
  post: jest.Mock;
  delete: jest.Mock;
};

describe("aiPoliciesStudio API — FE-S12-02", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it("loads meta", async () => {
    mockedApi.get.mockResolvedValueOnce({
      data: {
        object: "AiPolicySet",
        capability: "CAP-091",
        reuses: ["AI-GR-001"],
        guardrail_catalog: { "AI-GR-001": "PII" },
        data_classes: ["public"],
        model_tiers: ["economy"],
        feature_ai_copilot: false,
        honesty: "no live LLM",
      },
    });
    const meta = await getAiPoliciesMeta("tenant-1");
    expect(meta.feature_ai_copilot).toBe(false);
    expect(mockedApi.get).toHaveBeenCalledWith("/api/v1/studio/ai-policies/meta", {
      headers: { "X-Tenant-Id": "tenant-1" },
    });
  });

  it("lists / gets / upserts / deletes / evaluates", async () => {
    const row = {
      id: "pol-1",
      tenant_id: "tenant-1",
      name: "Default",
      guardrails: { "AI-GR-001": true },
      data_class_rules: [
        {
          data_class: "pii",
          max_model_tier: "economy",
          require_pii_scrub: true,
        },
      ],
      schema_version: 1,
    };
    mockedApi.get.mockResolvedValueOnce({ data: [row] }).mockResolvedValueOnce({ data: row });
    mockedApi.post.mockResolvedValueOnce({ data: row }).mockResolvedValueOnce({
      data: {
        allowed: false,
        data_class: "pii",
        requested_model_tier: "full",
        max_model_tier: "economy",
        require_pii_scrub: true,
        sanitized_preview: "",
        redactions: {},
        findings: ["AI-GR-004:tier"],
        live_llm: false,
        feature_ai_copilot: false,
      },
    });
    mockedApi.delete.mockResolvedValueOnce({
      data: { deleted: true, id: "pol-1" },
    });

    await listAiPolicies("tenant-1");
    expect(mockedApi.get).toHaveBeenCalledWith("/api/v1/studio/ai-policies", {
      headers: { "X-Tenant-Id": "tenant-1" },
    });

    await getAiPolicy("tenant-1", "pol-1");
    expect(mockedApi.get).toHaveBeenCalledWith("/api/v1/studio/ai-policies/pol-1", {
      headers: { "X-Tenant-Id": "tenant-1" },
    });

    await upsertAiPolicy("tenant-1", {
      name: "Default",
      guardrails: { "AI-GR-001": true },
    });
    expect(mockedApi.post).toHaveBeenCalledWith(
      "/api/v1/studio/ai-policies",
      { name: "Default", guardrails: { "AI-GR-001": true } },
      { headers: { "X-Tenant-Id": "tenant-1" } }
    );

    await evaluateAiPolicy("tenant-1", {
      data_class: "pii",
      requested_model_tier: "full",
      sample_text: "ssn",
      policy_id: "pol-1",
    });
    expect(mockedApi.post).toHaveBeenCalledWith(
      "/api/v1/studio/ai-policies/evaluate",
      {
        data_class: "pii",
        requested_model_tier: "full",
        sample_text: "ssn",
        policy_id: "pol-1",
      },
      { headers: { "X-Tenant-Id": "tenant-1" } }
    );

    await deleteAiPolicy("tenant-1", "pol-1");
    expect(mockedApi.delete).toHaveBeenCalledWith("/api/v1/studio/ai-policies/pol-1", {
      headers: { "X-Tenant-Id": "tenant-1" },
    });
  });
});
