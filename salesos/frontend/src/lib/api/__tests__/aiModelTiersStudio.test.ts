import {
  getAiModelTierCatalog,
  getAiModelTierDefaults,
  resolveAiModelTiers,
} from "../aiModelTiersStudio";

jest.mock("../client", () => ({
  __esModule: true,
  default: { get: jest.fn() },
}));

import api from "../client";

const mocked = api as unknown as { get: jest.Mock };

describe("aiModelTiersStudio API — FE-S12-04", () => {
  beforeEach(() => {
    mocked.get.mockReset();
  });

  it("GETs catalog + defaults + resolve", async () => {
    mocked.get.mockResolvedValueOnce({
      data: {
        catalog: [
          {
            tier: "economy",
            label: "Economy",
            provider: "openai",
            model: "gpt-4o-mini",
            description: "cheap",
          },
        ],
        feature_ai_copilot: false,
        honesty: "Catalog only",
      },
    });
    const catalog = await getAiModelTierCatalog("tenant-1");
    expect(mocked.get).toHaveBeenCalledWith(
      "/api/v1/studio/ai-model-tiers/catalog",
      expect.any(Object)
    );
    expect(catalog.feature_ai_copilot).toBe(false);

    mocked.get.mockResolvedValueOnce({
      data: {
        plan_tier: "starter",
        ai_model_tier: { default: "economy", allowed: ["economy"] },
        resolved: {
          default_tier: "economy",
          allowed_tiers: ["economy"],
          selected_tier: "economy",
          provider: "openai",
          model: "gpt-4o-mini",
        },
        feature_ai_copilot: false,
      },
    });
    await getAiModelTierDefaults("tenant-1", "starter");
    expect(mocked.get).toHaveBeenCalledWith(
      "/api/v1/studio/ai-model-tiers/defaults",
      expect.objectContaining({ params: { plan_tier: "starter" } })
    );

    mocked.get.mockResolvedValueOnce({
      data: {
        feature_ai_copilot: false,
        plan_tier: "growth",
        source: "plan",
        default_tier: "standard",
        allowed_tiers: ["economy", "standard"],
        selected_tier: "standard",
        provider: "anthropic",
        model: "claude-3-5-haiku-20241022",
        catalog: [],
        honesty: "gated",
      },
    });
    const resolved = await resolveAiModelTiers("tenant-1", "standard");
    expect(mocked.get).toHaveBeenCalledWith(
      "/api/v1/studio/ai-model-tiers",
      expect.objectContaining({
        params: { requested_tier: "standard" },
      })
    );
    expect(resolved.selected_tier).toBe("standard");
    expect(resolved.feature_ai_copilot).toBe(false);
  });
});
