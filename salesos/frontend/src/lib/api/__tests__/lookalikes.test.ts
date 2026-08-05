import { getLookalikeMeta, listLookalikeRuns, runLookalikes } from "../lookalikes";

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

describe("lookalikes API — FE-S11-04", () => {
  beforeEach(() => {
    mocked.get.mockReset();
    mocked.post.mockReset();
  });

  it("GETs tip meta + list", async () => {
    mocked.get.mockResolvedValueOnce({
      data: {
        object: "LookalikeModel",
        training: "tenant won/lost",
        features: ["industry", "city"],
        honesty: "CI fixtures",
      },
    });
    const meta = await getLookalikeMeta("tenant-1");
    expect(mocked.get).toHaveBeenCalledWith("/api/v1/gtm/lookalikes/meta", expect.any(Object));
    expect(meta.object).toBe("LookalikeModel");

    mocked.get.mockResolvedValueOnce({ data: [] });
    await listLookalikeRuns("tenant-1");
    expect(mocked.get).toHaveBeenCalledWith("/api/v1/gtm/lookalikes", expect.any(Object));
  });

  it("POSTs run lookalikes", async () => {
    mocked.post.mockResolvedValueOnce({
      data: {
        id: "lk1",
        tenant_id: "tenant-1",
        name: "Pilot",
        seed: {
          company_name: "Acme",
          industry: "technology",
          city: "riyadh",
          employees_count: 50,
        },
        hits: [
          {
            company_id: "c1",
            company_name: "Beta Co",
            industry: "technology",
            city: "riyadh",
            employees_count: 40,
            similarity: 0.9,
            outcome_affinity: "won",
            matched_features: ["industry", "city"],
          },
        ],
        trained_on_won: 3,
        trained_on_lost: 2,
        schema_version: 1,
        hit_count: 1,
      },
    });
    const row = await runLookalikes("tenant-1", {
      name: "Pilot",
      company_name: "Acme",
      industry: "technology",
    });
    expect(mocked.post).toHaveBeenCalledWith(
      "/api/v1/gtm/lookalikes",
      expect.objectContaining({ company_name: "Acme" }),
      expect.any(Object)
    );
    expect(row.hit_count).toBe(1);
    expect(row.hits[0].similarity).toBeCloseTo(0.9);
  });
});
