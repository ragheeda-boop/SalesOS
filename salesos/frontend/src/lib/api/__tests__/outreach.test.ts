import {
  createOutreachDraft,
  getOutreachDraft,
  getOutreachMeta,
  listOutreachDrafts,
} from "../outreach";

jest.mock("../client", () => ({
  __esModule: true,
  default: { get: jest.fn(), post: jest.fn() },
}));

import api from "../client";

const mocked = api as unknown as { get: jest.Mock; post: jest.Mock };

describe("outreach API — FE-S11-08", () => {
  beforeEach(() => {
    mocked.get.mockReset();
    mocked.post.mockReset();
  });

  it("GETs meta + list + detail; POSTs draft", async () => {
    mocked.get.mockResolvedValueOnce({
      data: {
        object: "OutreachDraft",
        capability: "CAP-103",
        prompt_id: "gtm.ai_outreach.v1",
        prompt_version: "1",
        channels: ["email"],
        intents: ["intro"],
        spend_path: "platform_llm_budget",
        generators_configured: ["fixture_outreach"],
        delivery_status: "draft_only",
        feature_ai_copilot: false,
        honesty: "CI fixture only",
      },
    });
    const meta = await getOutreachMeta("tenant-1");
    expect(mocked.get).toHaveBeenCalledWith("/api/v1/gtm/outreach/meta", expect.any(Object));
    expect(meta.feature_ai_copilot).toBe(false);
    expect(meta.delivery_status).toBe("draft_only");

    const draft = {
      id: "or-1",
      tenant_id: "tenant-1",
      request: { company_name: "Acme" },
      subject: "Hello Acme",
      body: "Draft body",
      channel: "email",
      prompt_id: "gtm.ai_outreach.v1",
      prompt_version: "1",
      spend_path: "platform_llm_budget",
      generator_key: "fixture_outreach",
      delivery_status: "draft_only",
      schema_version: 1,
      warnings: [],
    };

    mocked.get.mockResolvedValueOnce({ data: [draft] });
    await listOutreachDrafts("tenant-1");
    expect(mocked.get).toHaveBeenCalledWith("/api/v1/gtm/outreach", expect.any(Object));

    mocked.get.mockResolvedValueOnce({ data: draft });
    await getOutreachDraft("tenant-1", "or-1");
    expect(mocked.get).toHaveBeenCalledWith("/api/v1/gtm/outreach/or-1", expect.any(Object));

    mocked.post.mockResolvedValueOnce({ data: draft });
    const row = await createOutreachDraft("tenant-1", {
      company_name: "Acme",
      channel: "email",
      intent: "intro",
    });
    expect(mocked.post).toHaveBeenCalledWith(
      "/api/v1/gtm/outreach",
      { company_name: "Acme", channel: "email", intent: "intro" },
      expect.any(Object)
    );
    expect(row.delivery_status).toBe("draft_only");
  });
});
