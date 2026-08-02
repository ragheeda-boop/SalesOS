import {
  checkPermissionsCeiling,
  getPermissionsCeiling,
  listCustomRoles,
  listPermissionsCatalog,
  setPermissionsCeiling,
  upsertCustomRole,
} from "../permissionsStudio";

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

describe("permissionsStudio API — FE-S10-06", () => {
  beforeEach(() => {
    mocked.get.mockReset();
    mocked.post.mockReset();
    mocked.put.mockReset();
  });

  it("GETs tip permissions catalog", async () => {
    mocked.get.mockResolvedValue({ data: [] });
    await listPermissionsCatalog("tenant-1");
    expect(mocked.get).toHaveBeenCalledWith(
      "/api/v1/studio/permissions/catalog",
      expect.objectContaining({
        headers: { "X-Tenant-Id": "tenant-1" },
      }),
    );
  });

  it("GETs tip ceiling summary", async () => {
    mocked.get.mockResolvedValue({
      data: {
        enabled_domains: ["DOM-001"],
        publish_domains: [],
        grantable_permissions: ["crm.companies.read"],
      },
    });
    const row = await getPermissionsCeiling("tenant-1");
    expect(mocked.get).toHaveBeenCalledWith(
      "/api/v1/studio/permissions/ceiling",
      expect.any(Object),
    );
    expect(row.grantable_permissions).toContain("crm.companies.read");
  });

  it("PUTs tip ceiling", async () => {
    mocked.put.mockResolvedValue({
      data: {
        enabled_domains: [],
        publish_domains: [],
        grantable_permissions: [],
        version: 1,
      },
    });
    await setPermissionsCeiling("tenant-1", { plan_tier: "starter" });
    expect(mocked.put).toHaveBeenCalledWith(
      "/api/v1/studio/permissions/ceiling",
      { plan_tier: "starter" },
      expect.objectContaining({
        headers: { "X-Tenant-Id": "tenant-1" },
      }),
    );
  });

  it("POSTs tip ceiling check", async () => {
    mocked.post.mockResolvedValue({
      data: {
        allowed: false,
        rejected: ["ai.rag.use"],
        reasons: { "ai.rag.use": "DOM-011" },
        grantable: [],
      },
    });
    const row = await checkPermissionsCeiling("tenant-1", {
      permissions: ["ai.rag.use"],
      plan_tier: "starter",
    });
    expect(mocked.post).toHaveBeenCalledWith(
      "/api/v1/studio/permissions/check",
      expect.objectContaining({ plan_tier: "starter" }),
      expect.any(Object),
    );
    expect(row.allowed).toBe(false);
  });

  it("lists and upserts tip custom roles", async () => {
    mocked.get.mockResolvedValue({ data: [] });
    await listCustomRoles("tenant-1");
    expect(mocked.get).toHaveBeenCalledWith(
      "/api/v1/studio/permissions/roles",
      expect.any(Object),
    );

    mocked.post.mockResolvedValue({
      data: {
        id: "r1",
        tenant_id: "t1",
        name: "Seller",
        description: "",
        permissions: ["crm.companies.read"],
        schema_version: 1,
      },
    });
    const role = await upsertCustomRole("tenant-1", {
      name: "Seller",
      permissions: ["crm.companies.read"],
    });
    expect(mocked.post).toHaveBeenCalledWith(
      "/api/v1/studio/permissions/roles",
      expect.objectContaining({ name: "Seller" }),
      expect.any(Object),
    );
    expect(role.id).toBe("r1");
  });
});
