import {
  getLeadDiscoveryMeta,
  listLeadDiscovery,
  runLeadDiscovery,
} from "../leadDiscovery";

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

describe("leadDiscovery API — FE-S11-03", () => {
  beforeEach(() => {
    mocked.get.mockReset();
    mocked.post.mockReset();
  });

  it("GETs tip meta + list", async () => {
    mocked.get.mockResolvedValueOnce({
      data: {
        dataset_scale_hint: 141221,
        filters: ["industries"],
        sourcing_order: ["government", "provider_via_integration_hub"],
        honesty: "in-memory",
      },
    });
    const meta = await getLeadDiscoveryMeta("tenant-1");
    expect(mocked.get).toHaveBeenCalledWith(
      "/api/v1/gtm/lead-discovery/meta",
      expect.any(Object),
    );
    expect(meta.sourcing_order[0]).toBe("government");

    mocked.get.mockResolvedValueOnce({ data: [] });
    await listLeadDiscovery("tenant-1");
    expect(mocked.get).toHaveBeenCalledWith(
      "/api/v1/gtm/lead-discovery",
      expect.any(Object),
    );
  });

  it("POSTs tip discover", async () => {
    mocked.post.mockResolvedValueOnce({
      data: {
        id: "ld1",
        tenant_id: "tenant-1",
        name: "Pilot",
        query: {
          industries: ["technology"],
          cities: ["riyadh"],
          employees_min: 10,
          employees_max: 100,
          limit: 25,
        },
        leads: [
          {
            id: "l1",
            company_name: "Acme",
            industry: "technology",
            city: "riyadh",
            employees_count: 50,
            source: "government",
            external_id: "",
          },
        ],
        government_hit_count: 1,
        provider_hit_count: 0,
        provider_key: "",
        dataset_scale_hint: 141221,
        schema_version: 1,
        government_first_ok: true,
        total_hits: 1,
      },
    });
    const row = await runLeadDiscovery("tenant-1", {
      name: "Pilot",
      industries: ["technology"],
      cities: ["riyadh"],
      limit: 25,
    });
    expect(mocked.post).toHaveBeenCalledWith(
      "/api/v1/gtm/lead-discovery",
      expect.objectContaining({ name: "Pilot" }),
      expect.any(Object),
    );
    expect(row.government_first_ok).toBe(true);
    expect(row.leads[0].source).toBe("government");
  });
});
