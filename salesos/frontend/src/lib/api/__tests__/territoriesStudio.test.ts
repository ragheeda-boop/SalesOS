import {
  assignTerritory,
  getTerritoriesMeta,
  listTerritoryRules,
  upsertTerritoryRule,
} from "../territoriesStudio";

jest.mock("../client", () => ({
  __esModule: true,
  default: { get: jest.fn(), post: jest.fn(), delete: jest.fn() },
}));

import api from "../client";

const mocked = api as unknown as {
  get: jest.Mock;
  post: jest.Mock;
  delete: jest.Mock;
};

describe("territoriesStudio API — FE-S10-05", () => {
  beforeEach(() => {
    mocked.get.mockReset();
    mocked.post.mockReset();
    mocked.delete.mockReset();
  });

  it("GETs tip meta + list", async () => {
    mocked.get.mockResolvedValueOnce({
      data: {
        match_fields: ["region", "industry"],
        match_ops: ["eq", "gte"],
        dimensions: ["geography", "industry", "size"],
        persistence: "memory",
        runtime: "CAP-017",
        policy_count_delta: 0,
      },
    });
    const meta = await getTerritoriesMeta("tenant-1");
    expect(mocked.get).toHaveBeenCalledWith(
      "/api/v1/studio/territories/meta",
      expect.any(Object),
    );
    expect(meta.persistence).toBe("memory");

    mocked.get.mockResolvedValueOnce({ data: [] });
    await listTerritoryRules("tenant-1");
    expect(mocked.get).toHaveBeenCalledWith(
      "/api/v1/studio/territories",
      expect.any(Object),
    );
  });

  it("POSTs upsert + assign", async () => {
    mocked.post.mockResolvedValueOnce({
      data: {
        id: "r1",
        tenant_id: "tenant-1",
        name: "Riyadh North",
        territory_key: "riyadh-north",
        region: "Riyadh",
        rep_id: "rep-1",
        priority: 10,
        match_conditions: [{ field: "region", op: "eq", value: "Riyadh" }],
        active: true,
        schema_version: 1,
      },
    });
    await upsertTerritoryRule("tenant-1", {
      name: "Riyadh North",
      territory_key: "riyadh-north",
      match_conditions: [{ field: "region", op: "eq", value: "Riyadh" }],
    });
    expect(mocked.post).toHaveBeenCalledWith(
      "/api/v1/studio/territories",
      expect.objectContaining({ territory_key: "riyadh-north" }),
      expect.any(Object),
    );

    mocked.post.mockResolvedValueOnce({
      data: {
        matched: true,
        territory_key: "riyadh-north",
        rule_id: "r1",
        region: "Riyadh",
        rep_id: "rep-1",
        source: "tenant_rule",
        explanation: ["matched region eq Riyadh"],
      },
    });
    const hit = await assignTerritory("tenant-1", {
      attributes: { region: "Riyadh" },
    });
    expect(mocked.post).toHaveBeenCalledWith(
      "/api/v1/studio/territories/assign",
      expect.objectContaining({ attributes: { region: "Riyadh" } }),
      expect.any(Object),
    );
    expect(hit.matched).toBe(true);
  });
});
