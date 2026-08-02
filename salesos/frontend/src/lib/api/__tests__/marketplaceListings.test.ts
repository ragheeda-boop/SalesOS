import {
  getMarketplaceListing,
  getMarketplaceListingsMeta,
  listMarketplaceListings,
  seedFirstPartyMarketplaceListings,
} from "../marketplaceListings";

jest.mock("../client", () => ({
  __esModule: true,
  default: { get: jest.fn(), post: jest.fn() },
}));

import api from "../client";

const mocked = api as unknown as { get: jest.Mock; post: jest.Mock };

describe("marketplaceListings API — FE-S13-01b", () => {
  beforeEach(() => {
    mocked.get.mockReset();
    mocked.post.mockReset();
  });

  it("GETs meta + list + detail; POSTs seed", async () => {
    mocked.get.mockResolvedValueOnce({
      data: {
        listing_types: ["connector"],
        statuses: ["draft"],
        object: "MarketplaceListing",
        obj_id: "OBJ-325",
        persistence: "memory",
        policy_count_delta: 0,
        honesty: "Catalog object only",
      },
    });
    const meta = await getMarketplaceListingsMeta("tenant-1");
    expect(mocked.get).toHaveBeenCalledWith(
      "/api/v1/marketplace/listings/meta",
      expect.any(Object),
    );
    expect(meta.persistence).toBe("memory");

    mocked.get.mockResolvedValueOnce({
      data: [
        {
          id: "ml-1",
          slug: "odoo-connector",
          name: "Odoo",
          listing_type: "connector",
          version: "1.0.0",
          status: "published",
          description: "",
          publisher: "SalesOS",
          first_party: true,
          connector_key: "odoo",
          tags: [],
          manifest: {},
          schema_version: 1,
        },
      ],
    });
    const rows = await listMarketplaceListings("tenant-1", {
      listing_type: "connector",
    });
    expect(mocked.get).toHaveBeenCalledWith(
      "/api/v1/marketplace/listings",
      expect.objectContaining({
        params: { listing_type: "connector" },
      }),
    );
    expect(rows).toHaveLength(1);

    mocked.get.mockResolvedValueOnce({ data: rows[0] });
    await getMarketplaceListing("tenant-1", "odoo-connector");
    expect(mocked.get).toHaveBeenCalledWith(
      "/api/v1/marketplace/listings/odoo-connector",
      expect.any(Object),
    );

    mocked.post.mockResolvedValueOnce({ data: rows });
    const seeded = await seedFirstPartyMarketplaceListings("tenant-1");
    expect(mocked.post).toHaveBeenCalledWith(
      "/api/v1/marketplace/listings/seed-first-party",
      {},
      expect.any(Object),
    );
    expect(seeded).toHaveLength(1);
  });
});
