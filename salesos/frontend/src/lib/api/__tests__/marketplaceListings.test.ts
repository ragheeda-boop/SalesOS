import {
  certifyMarketplaceListing,
  getMarketplaceCertifyMeta,
  getMarketplaceListing,
  getMarketplaceListingsMeta,
  installMarketplaceListing,
  listMarketplaceCatalogInstalls,
  listMarketplaceListings,
  publishMarketplaceListing,
  seedFirstPartyMarketplaceListings,
  seedMarketplacePublishPack,
  submitMarketplaceListing,
} from "../marketplaceListings";

jest.mock("../client", () => ({
  __esModule: true,
  default: { get: jest.fn(), post: jest.fn() },
}));

import api from "../client";

const mocked = api as unknown as { get: jest.Mock; post: jest.Mock };

describe("marketplaceListings API — FE-S13-04", () => {
  beforeEach(() => {
    mocked.get.mockReset();
    mocked.post.mockReset();
  });

  it("GETs meta/list/detail/certify/meta/installs; POSTs seed/publish/install", async () => {
    mocked.get.mockResolvedValueOnce({
      data: {
        listing_types: ["connector"],
        statuses: ["published"],
        object: "MarketplaceListing",
        obj_id: "OBJ-325",
        persistence: "memory",
        policy_count_delta: 0,
        honesty: "Catalog install ≠ live sync",
        publish_pack: {
          story: "STORY-13-04",
          min_connectors: 3,
          min_playbooks: 1,
          seed_slugs: ["connector-odoo"],
          connector_keys: ["odoo"],
        },
      },
    });
    const meta = await getMarketplaceListingsMeta("tenant-1");
    expect(meta.persistence).toBe("memory");
    expect(meta.publish_pack?.story).toBe("STORY-13-04");

    mocked.get.mockResolvedValueOnce({
      data: [
        {
          id: "ml-1",
          slug: "connector-odoo",
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
          installable: true,
        },
      ],
    });
    const rows = await listMarketplaceListings("tenant-1");
    expect(rows[0].installable).toBe(true);

    mocked.get.mockResolvedValueOnce({ data: rows[0] });
    await getMarketplaceListing("tenant-1", "connector-odoo");

    mocked.get.mockResolvedValueOnce({
      data: {
        capability: "CAP-094",
        stages: ["conformance"],
        conformance_suite: "certify_source_connector",
        via: "/api/v1/integrations/certify/{connector_key}",
        trial_sandbox: "marketplace_listings.trial_sandbox",
        not_domains_marketplace_sandbox: true,
        first_party_checklist_exception: false,
        feature_ai_copilot: false,
        honesty: "CI only",
      },
    });
    await getMarketplaceCertifyMeta("tenant-1");

    mocked.get.mockResolvedValueOnce({ data: [] });
    await listMarketplaceCatalogInstalls("tenant-1");
    expect(mocked.get).toHaveBeenCalledWith(
      "/api/v1/marketplace/listings/installs",
      expect.any(Object)
    );

    mocked.post.mockResolvedValueOnce({ data: rows });
    await seedMarketplacePublishPack("tenant-1");
    expect(mocked.post).toHaveBeenCalledWith(
      "/api/v1/marketplace/listings/seed-publish-pack",
      {},
      expect.any(Object)
    );

    mocked.post.mockResolvedValueOnce({ data: rows });
    await seedFirstPartyMarketplaceListings("tenant-1");

    mocked.post.mockResolvedValueOnce({
      data: { ...rows[0], status: "published", installable: true },
    });
    await publishMarketplaceListing("tenant-1", "ml-1");
    expect(mocked.post).toHaveBeenCalledWith(
      "/api/v1/marketplace/listings/ml-1/publish",
      {},
      expect.any(Object)
    );

    mocked.post.mockResolvedValueOnce({
      data: {
        id: "inst-1",
        tenant_id: "tenant-1",
        listing_id: "ml-1",
        listing_slug: "connector-odoo",
        listing_type: "connector",
        connector_key: "odoo",
        installed_at: "2026-08-02T00:00:00Z",
        honesty: "Catalog install receipt only",
      },
    });
    const install = await installMarketplaceListing("tenant-1", "ml-1");
    expect(mocked.post).toHaveBeenCalledWith(
      "/api/v1/marketplace/listings/ml-1/install",
      {},
      expect.any(Object)
    );
    expect(install.listing_slug).toBe("connector-odoo");

    mocked.post.mockResolvedValueOnce({
      data: { ...rows[0], status: "pending_certification" },
    });
    await submitMarketplaceListing("tenant-1", "ml-1");

    mocked.post.mockResolvedValueOnce({
      data: {
        listing_id: "ml-1",
        ok: true,
        status_before: "pending_certification",
        status_after: "certified",
        stages: [],
        ran_at: "2026-08-02T00:00:00Z",
        honesty: "CI only",
      },
    });
    await certifyMarketplaceListing("tenant-1", "ml-1", { auto_submit: true });
  });
});
