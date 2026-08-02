import {
  certifyMarketplaceListing,
  getMarketplaceCertifyMeta,
  getMarketplaceListing,
  getMarketplaceListingsMeta,
  listMarketplaceListings,
  seedFirstPartyMarketplaceListings,
  submitMarketplaceListing,
} from "../marketplaceListings";

jest.mock("../client", () => ({
  __esModule: true,
  default: { get: jest.fn(), post: jest.fn() },
}));

import api from "../client";

const mocked = api as unknown as { get: jest.Mock; post: jest.Mock };

describe("marketplaceListings API — FE-S13-03", () => {
  beforeEach(() => {
    mocked.get.mockReset();
    mocked.post.mockReset();
  });

  it("GETs meta + list + detail + certify/meta; POSTs seed/submit/certify", async () => {
    mocked.get.mockResolvedValueOnce({
      data: {
        listing_types: ["connector"],
        statuses: ["draft"],
        object: "MarketplaceListing",
        obj_id: "OBJ-325",
        persistence: "memory",
        policy_count_delta: 0,
        honesty: "Catalog object only",
        certify_stages: ["conformance"],
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
          status: "draft",
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
    expect(rows).toHaveLength(1);

    mocked.get.mockResolvedValueOnce({ data: rows[0] });
    await getMarketplaceListing("tenant-1", "odoo-connector");

    mocked.get.mockResolvedValueOnce({
      data: {
        capability: "CAP-094",
        stages: ["conformance", "security_checklist", "sandboxed_trial"],
        conformance_suite: "certify_source_connector",
        via: "/api/v1/integrations/certify/{connector_key}",
        trial_sandbox: "marketplace_listings.trial_sandbox",
        not_domains_marketplace_sandbox: true,
        first_party_checklist_exception: false,
        feature_ai_copilot: false,
        honesty: "CI pipeline only",
      },
    });
    const certifyMeta = await getMarketplaceCertifyMeta("tenant-1");
    expect(mocked.get).toHaveBeenCalledWith(
      "/api/v1/marketplace/listings/certify/meta",
      expect.any(Object),
    );
    expect(certifyMeta.feature_ai_copilot).toBe(false);

    mocked.post.mockResolvedValueOnce({ data: rows });
    await seedFirstPartyMarketplaceListings("tenant-1");

    mocked.post.mockResolvedValueOnce({
      data: { ...rows[0], status: "pending_certification" },
    });
    await submitMarketplaceListing("tenant-1", "ml-1");
    expect(mocked.post).toHaveBeenCalledWith(
      "/api/v1/marketplace/listings/ml-1/submit",
      {},
      expect.any(Object),
    );

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
    const report = await certifyMarketplaceListing("tenant-1", "ml-1", {
      auto_submit: true,
    });
    expect(mocked.post).toHaveBeenCalledWith(
      "/api/v1/marketplace/listings/ml-1/certify",
      { real_tenant_ids: [], auto_submit: true },
      expect.any(Object),
    );
    expect(report.ok).toBe(true);
  });
});
