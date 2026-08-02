import {
  computeMarketSizing,
  getMarketSizing,
  getMarketSizingMeta,
  listMarketSizing,
} from "../marketSizing";

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

describe("marketSizing API — FE-S11-02", () => {
  beforeEach(() => {
    mocked.get.mockReset();
    mocked.post.mockReset();
  });

  it("GETs tip meta + list", async () => {
    mocked.get.mockResolvedValueOnce({
      data: {
        dataset_scale_hint: 141221,
        filters: ["industries"],
        invariant: "SOM <= SAM <= TAM",
        honesty: "in-memory",
      },
    });
    const meta = await getMarketSizingMeta("tenant-1");
    expect(mocked.get).toHaveBeenCalledWith(
      "/api/v1/gtm/market-sizing/meta",
      expect.any(Object),
    );
    expect(meta.dataset_scale_hint).toBe(141221);

    mocked.get.mockResolvedValueOnce({ data: [] });
    await listMarketSizing("tenant-1");
    expect(mocked.get).toHaveBeenCalledWith(
      "/api/v1/gtm/market-sizing",
      expect.any(Object),
    );
  });

  it("POSTs tip compute", async () => {
    mocked.post.mockResolvedValueOnce({
      data: {
        id: "ms1",
        tenant_id: "tenant-1",
        name: "Pilot",
        criteria: {
          industries: ["tech"],
          cities: ["riyadh"],
          employees_min: 10,
          employees_max: 100,
        },
        tam: 50,
        sam: 20,
        som: 5,
        universe_size: 250,
        dataset_scale_hint: 141221,
        schema_version: 1,
        invariant_ok: true,
      },
    });
    const row = await computeMarketSizing("tenant-1", {
      name: "Pilot",
      industries: ["tech"],
      cities: ["riyadh"],
      employees_min: 10,
      employees_max: 100,
    });
    expect(mocked.post).toHaveBeenCalledWith(
      "/api/v1/gtm/market-sizing",
      expect.objectContaining({ name: "Pilot" }),
      expect.any(Object),
    );
    expect(row.som).toBe(5);
    expect(row.invariant_ok).toBe(true);
  });

  it("GETs tip snapshot detail", async () => {
    mocked.get.mockResolvedValueOnce({
      data: {
        id: "ms1",
        tenant_id: "tenant-1",
        name: "Pilot",
        criteria: {
          industries: ["tech"],
          cities: ["riyadh"],
          employees_min: 10,
          employees_max: 100,
        },
        tam: 50,
        sam: 20,
        som: 5,
        universe_size: 250,
        dataset_scale_hint: 141221,
        schema_version: 1,
        invariant_ok: true,
      },
    });
    const row = await getMarketSizing("tenant-1", "ms1");
    expect(mocked.get).toHaveBeenCalledWith(
      "/api/v1/gtm/market-sizing/ms1",
      expect.any(Object),
    );
    expect(row.id).toBe("ms1");
  });
});
