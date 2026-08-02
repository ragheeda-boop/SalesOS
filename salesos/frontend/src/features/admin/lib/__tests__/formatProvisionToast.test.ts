import {
  activityStatusLabel,
  buildAdminTenantsFilterQuery,
  formatActivateResultDescription,
  formatReprovisionResultDescription,
  formatTrialEndsLabel,
  getDeletionRequestedAt,
  parseAdminTenantsPageSize,
  retentionHardDeleteDescription,
  suspendedWriteBlockDescription,
  lifecycleStatusDescription,
  matchesTrialFilter,
  sortAdminTenants,
  trialBadgeLabel,
  trialBadgeVariant,
  trialBucket,
  formatProvisionResultDescription,
  formatSuspendResultDescription,
} from "../formatProvisionToast";

describe("formatProvisionResultDescription", () => {
  it("summarizes Owner Platform fields from create response", () => {
    expect(
      formatProvisionResultDescription({
        slug: "acme",
        plan_id: "cat-1",
        region: "me-central-1",
        data_residency: "ae",
        provisioning_status: "active",
        trial_ends_at: null,
      }),
    ).toBe(
      "slug=acme · provisioning=active · plan_id=cat-1 · region=me-central-1 · residency=ae",
    );
  });

  it("defaults provisioning when missing", () => {
    expect(
      formatProvisionResultDescription({
        slug: "x",
        plan_id: null,
        region: null,
        data_residency: null,
        provisioning_status: "",
        trial_ends_at: null,
      }),
    ).toBe("slug=x · provisioning=pending");
  });
});

describe("formatSuspendResultDescription", () => {
  it("includes reason when provided", () => {
    expect(formatSuspendResultDescription("t-1", "Owner Console")).toBe(
      "tenant_id=t-1 · is_active=false · provisioning=suspended · reason=Owner Console",
    );
  });
});

describe("formatActivateResultDescription — FE-S04-27", () => {
  it("summarizes activate response fields", () => {
    expect(
      formatActivateResultDescription({
        tenant_id: "t-1",
        prior_provisioning_status: "suspended",
        provisioning_status: "active",
        reason: "Owner Console",
      }),
    ).toBe(
      "tenant_id=t-1 · is_active=true · prior=suspended · provisioning=active · reason=Owner Console",
    );
  });
});

describe("activityStatusLabel — FE-S04-13", () => {
  it("labels active tenants", () => {
    expect(
      activityStatusLabel({ is_active: true, provisioning_status: "active" }),
    ).toBe("Active");
  });

  it("labels suspend path as Suspended", () => {
    expect(
      activityStatusLabel({
        is_active: false,
        provisioning_status: "suspended",
      }),
    ).toBe("Suspended");
  });

  it("labels soft-delete as Inactive (not Suspended)", () => {
    expect(
      activityStatusLabel({ is_active: false, provisioning_status: "active" }),
    ).toBe("Inactive");
  });
});

describe("trial helpers — FE-S04-15", () => {
  const now = Date.parse("2026-08-02T00:00:00.000Z");

  it("buckets none / has_trial / expired", () => {
    expect(trialBucket(null, now)).toBe("none");
    expect(trialBucket("2026-09-01T00:00:00.000Z", now)).toBe("has_trial");
    expect(trialBucket("2026-07-01T00:00:00.000Z", now)).toBe("expired");
  });

  it("matches trial filter", () => {
    expect(matchesTrialFilter(null, "", now)).toBe(true);
    expect(matchesTrialFilter(null, "none", now)).toBe(true);
    expect(
      matchesTrialFilter("2026-09-01T00:00:00.000Z", "has_trial", now),
    ).toBe(true);
    expect(matchesTrialFilter("2026-07-01T00:00:00.000Z", "expired", now)).toBe(
      true,
    );
  });

  it("formats trial label", () => {
    expect(formatTrialEndsLabel(null)).toBe("—");
    expect(formatTrialEndsLabel("not-a-date")).toBe("—");
  });

  it("FE-S04-25 trial badge label/variant", () => {
    expect(trialBadgeLabel(null, now)).toBe("No trial");
    expect(trialBadgeVariant(null, now)).toBe("default");
    expect(trialBadgeLabel("2026-09-01T00:00:00.000Z", now)).toBe(
      "Active trial",
    );
    expect(trialBadgeVariant("2026-09-01T00:00:00.000Z", now)).toBe("success");
    expect(trialBadgeLabel("2026-07-01T00:00:00.000Z", now)).toBe("Expired");
    expect(trialBadgeVariant("2026-07-01T00:00:00.000Z", now)).toBe("warning");
  });
});

describe("lifecycleStatusDescription — FE-S04-17", () => {
  it("describes active / suspended / soft-deleted", () => {
    expect(
      lifecycleStatusDescription({
        is_active: true,
        provisioning_status: "active",
      }),
    ).toContain("Active");
    expect(
      lifecycleStatusDescription({
        is_active: false,
        provisioning_status: "suspended",
      }),
    ).toContain("/suspend");
    expect(
      lifecycleStatusDescription({
        is_active: false,
        provisioning_status: "active",
      }),
    ).toContain("soft-deleted");
  });
});

describe("sortAdminTenants — FE-S04-19", () => {
  const rows = [
    { name: "Beta", created_at: "2026-01-02T00:00:00.000Z" },
    { name: "Alpha", created_at: "2026-01-03T00:00:00.000Z" },
    { name: "Gamma", created_at: "2026-01-01T00:00:00.000Z" },
  ];

  it("sorts by name and created_at", () => {
    expect(sortAdminTenants(rows, "name_asc").map((r) => r.name)).toEqual([
      "Alpha",
      "Beta",
      "Gamma",
    ]);
    expect(sortAdminTenants(rows, "created_desc").map((r) => r.name)).toEqual([
      "Alpha",
      "Beta",
      "Gamma",
    ]);
  });
});

describe("buildAdminTenantsFilterQuery — FE-S04-29/33", () => {
  it("omits default sort and page 1; includes page>1", () => {
    expect(
      buildAdminTenantsFilterQuery({
        search: " acme ",
        sort: "created_desc",
        page: 1,
        page_size: 20,
      }),
    ).toBe("search=acme");
    expect(
      buildAdminTenantsFilterQuery({
        status: "active",
        sort: "name_asc",
        page: 2,
      }),
    ).toBe("status=active&sort=name_asc&page=2");
  });
});

describe("formatReprovisionResultDescription — FE-S04-34", () => {
  it("summarizes reprovision response", () => {
    expect(
      formatReprovisionResultDescription({
        tenant_id: "t-1",
        slug: "acme",
        provisioning_status: "active",
        created: false,
        idempotent: true,
        roles_provisioned: 3,
        permissions_provisioned: 12,
      }),
    ).toBe(
      "tenant_id=t-1 · slug=acme · provisioning=active · created=false · idempotent=true · roles=3 · permissions=12",
    );
  });
});

describe("retention helpers — FE-S04-35", () => {
  it("reads deletion_requested_at from settings", () => {
    expect(
      getDeletionRequestedAt({
        deletion_requested_at: "2026-08-01T00:00:00+00:00",
      }),
    ).toBe("2026-08-01T00:00:00+00:00");
    expect(getDeletionRequestedAt({})).toBeNull();
  });

  it("describes retention / force_immediate honesty", () => {
    expect(
      retentionHardDeleteDescription({
        deletionRequestedAt: "2026-08-01T00:00:00Z",
        retentionDays: 30,
      }),
    ).toContain("force_immediate=true");
    expect(retentionHardDeleteDescription({ isInactive: true })).toContain(
      "soft-delete stamp",
    );
  });
});

describe("suspendedWriteBlockDescription — FE-S04-38", () => {
  it("returns honesty only when provisioning=suspended", () => {
    expect(
      suspendedWriteBlockDescription({ provisioning_status: "suspended" }),
    ).toContain("STORY-04-03");
    expect(
      suspendedWriteBlockDescription({ provisioning_status: "active" }),
    ).toBeNull();
  });
});

describe("parseAdminTenantsPageSize — FE-S04-39", () => {
  it("accepts 20/50/100 and defaults to 20", () => {
    expect(parseAdminTenantsPageSize("50")).toBe(50);
    expect(parseAdminTenantsPageSize("100")).toBe(100);
    expect(parseAdminTenantsPageSize("7")).toBe(20);
    expect(parseAdminTenantsPageSize(null)).toBe(20);
  });
});

describe("buildAdminTenantsFilterQuery page_size — FE-S04-39", () => {
  it("includes non-default page_size", () => {
    expect(buildAdminTenantsFilterQuery({ page: 1, page_size: 50 })).toBe(
      "page_size=50",
    );
  });
});
