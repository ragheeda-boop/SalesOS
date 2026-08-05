import {
  createIcpProfile,
  getIcpMeta,
  listIcpProfiles,
  scoreIcpProfile,
  updateIcpProfile,
} from "../icpProfiles";

jest.mock("../client", () => ({
  __esModule: true,
  default: {
    get: jest.fn(),
    post: jest.fn(),
    put: jest.fn(),
  },
}));

import api from "../client";

const mocked = api as unknown as {
  get: jest.Mock;
  post: jest.Mock;
  put: jest.Mock;
};

describe("icpProfiles API — FE-S11-01", () => {
  beforeEach(() => {
    mocked.get.mockReset();
    mocked.post.mockReset();
    mocked.put.mockReset();
  });

  it("GETs tip meta + list", async () => {
    mocked.get.mockResolvedValueOnce({
      data: {
        object: "ICPProfile",
        filters: ["industries"],
        versioning: "schema_version increments on PUT",
        scoring: "deterministic",
        honesty: "in-memory",
      },
    });
    const meta = await getIcpMeta("tenant-1");
    expect(mocked.get).toHaveBeenCalledWith("/api/v1/gtm/icp-profiles/meta", expect.any(Object));
    expect(meta.object).toBe("ICPProfile");

    mocked.get.mockResolvedValueOnce({ data: [] });
    await listIcpProfiles("tenant-1");
    expect(mocked.get).toHaveBeenCalledWith("/api/v1/gtm/icp-profiles", expect.any(Object));
  });

  it("POSTs create and PUTs update + score", async () => {
    mocked.post.mockResolvedValueOnce({
      data: {
        id: "icp1",
        tenant_id: "tenant-1",
        name: "Pilot",
        description: "",
        criteria: {
          industries: ["technology"],
          cities: ["riyadh"],
          employees_min: 10,
          employees_max: 100,
          titles: [],
          keywords: [],
        },
        weights: {
          industry: 1,
          city: 1,
          employees: 1,
          titles: 0.5,
          keywords: 0.5,
        },
        schema_version: 1,
        is_active: true,
      },
    });
    await createIcpProfile("tenant-1", {
      name: "Pilot",
      industries: ["technology"],
    });
    expect(mocked.post).toHaveBeenCalledWith(
      "/api/v1/gtm/icp-profiles",
      expect.objectContaining({ name: "Pilot" }),
      expect.any(Object)
    );

    mocked.put.mockResolvedValueOnce({
      data: {
        id: "icp1",
        tenant_id: "tenant-1",
        name: "Pilot v2",
        description: "",
        criteria: {
          industries: ["technology"],
          cities: [],
          employees_min: null,
          employees_max: null,
          titles: [],
          keywords: [],
        },
        weights: {
          industry: 1,
          city: 1,
          employees: 1,
          titles: 0.5,
          keywords: 0.5,
        },
        schema_version: 2,
        is_active: true,
      },
    });
    const updated = await updateIcpProfile("tenant-1", "icp1", {
      name: "Pilot v2",
    });
    expect(mocked.put).toHaveBeenCalledWith(
      "/api/v1/gtm/icp-profiles/icp1",
      expect.objectContaining({ name: "Pilot v2" }),
      expect.any(Object)
    );
    expect(updated.schema_version).toBe(2);

    mocked.post.mockResolvedValueOnce({
      data: {
        profile_id: "icp1",
        schema_version: 2,
        score: 2,
        max_score: 3,
        fit_ratio: 0.66,
        matched: { industry: true },
        company: {},
      },
    });
    const scored = await scoreIcpProfile("tenant-1", "icp1", {
      industry: "technology",
    });
    expect(mocked.post).toHaveBeenCalledWith(
      "/api/v1/gtm/icp-profiles/icp1/score",
      expect.objectContaining({ industry: "technology" }),
      expect.any(Object)
    );
    expect(scored.fit_ratio).toBeCloseTo(0.66);
  });
});
