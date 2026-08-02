import {
  getEnrichmentMeta,
  listEnrichmentRuns,
  runEnrichment,
} from "../enrichment";

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

describe("enrichment API — FE-S11-05", () => {
  beforeEach(() => {
    mocked.get.mockReset();
    mocked.post.mockReset();
  });

  it("GETs tip meta + list", async () => {
    mocked.get.mockResolvedValueOnce({
      data: {
        enrichable_fields: ["industry", "city"],
        providers_configured: ["fake_a", "fake_b"],
        policy: "first non-empty",
        honesty: "CI uses FakeEnrichment",
      },
    });
    const meta = await getEnrichmentMeta("tenant-1");
    expect(mocked.get).toHaveBeenCalledWith(
      "/api/v1/gtm/enrichment/meta",
      expect.any(Object),
    );
    expect(meta.providers_configured).toEqual(["fake_a", "fake_b"]);

    mocked.get.mockResolvedValueOnce({ data: [] });
    await listEnrichmentRuns("tenant-1");
    expect(mocked.get).toHaveBeenCalledWith(
      "/api/v1/gtm/enrichment",
      expect.any(Object),
    );
  });

  it("POSTs run enrichment", async () => {
    mocked.post.mockResolvedValueOnce({
      data: {
        id: "enr1",
        tenant_id: "tenant-1",
        request: {
          company_name: "Acme",
          domain: "acme.example",
          external_id: "",
          known: {},
          provider_order: [],
        },
        filled: { industry: "technology", city: "riyadh" },
        hits: [
          { field: "industry", value: "technology", provider_key: "fake_a" },
        ],
        providers_attempted: ["fake_a", "fake_b"],
        providers_configured: ["fake_a", "fake_b"],
        missing_fields: [],
        schema_version: 1,
        complete: true,
      },
    });
    const row = await runEnrichment("tenant-1", {
      company_name: "Acme",
      domain: "acme.example",
    });
    expect(mocked.post).toHaveBeenCalledWith(
      "/api/v1/gtm/enrichment",
      expect.objectContaining({ company_name: "Acme" }),
      expect.any(Object),
    );
    expect(row.complete).toBe(true);
    expect(row.filled.industry).toBe("technology");
  });
});
