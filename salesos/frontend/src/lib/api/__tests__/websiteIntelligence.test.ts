import {
  getWebsiteIntelligence,
  getWebsiteIntelligenceMeta,
  listWebsiteIntelligence,
  runWebsiteIntelligence,
} from "../websiteIntelligence";

jest.mock("../client", () => ({
  __esModule: true,
  default: { get: jest.fn(), post: jest.fn() },
}));

import api from "../client";

const mocked = api as unknown as { get: jest.Mock; post: jest.Mock };

describe("websiteIntelligence API — FE-S11-07", () => {
  beforeEach(() => {
    mocked.get.mockReset();
    mocked.post.mockReset();
  });

  it("GETs meta + list + detail; POSTs analyze", async () => {
    mocked.get.mockResolvedValueOnce({
      data: {
        object: "WebsiteIntelligenceSnapshot",
        capability: "CAP-101",
        prompt_id: "gtm.website_intelligence.v1",
        prompt_version: "1",
        spend_path: "platform_llm_budget",
        analyzers_configured: ["fixture_website"],
        feature_ai_copilot: false,
        honesty: "CI fixture only",
      },
    });
    const meta = await getWebsiteIntelligenceMeta("tenant-1");
    expect(mocked.get).toHaveBeenCalledWith(
      "/api/v1/gtm/website-intelligence/meta",
      expect.any(Object),
    );
    expect(meta.feature_ai_copilot).toBe(false);

    const snap = {
      id: "wi-1",
      tenant_id: "tenant-1",
      request: { url: "https://acme.example" },
      summary: "fixture",
      signals: [{ key: "industry", value: "saas", confidence: 0.8 }],
      prompt_id: "gtm.website_intelligence.v1",
      prompt_version: "1",
      spend_path: "platform_llm_budget",
      analyzer_key: "fixture_website",
      schema_version: 1,
      signal_count: 1,
    };

    mocked.get.mockResolvedValueOnce({ data: [snap] });
    await listWebsiteIntelligence("tenant-1");
    expect(mocked.get).toHaveBeenCalledWith(
      "/api/v1/gtm/website-intelligence",
      expect.any(Object),
    );

    mocked.get.mockResolvedValueOnce({ data: snap });
    await getWebsiteIntelligence("tenant-1", "wi-1");
    expect(mocked.get).toHaveBeenCalledWith(
      "/api/v1/gtm/website-intelligence/wi-1",
      expect.any(Object),
    );

    mocked.post.mockResolvedValueOnce({ data: snap });
    const row = await runWebsiteIntelligence("tenant-1", {
      url: "https://acme.example",
      company_name: "Acme",
    });
    expect(mocked.post).toHaveBeenCalledWith(
      "/api/v1/gtm/website-intelligence",
      { url: "https://acme.example", company_name: "Acme" },
      expect.any(Object),
    );
    expect(row.signal_count).toBe(1);
  });
});
