import {
  activityStatusLabel,
  formatActivateResultDescription,
  formatTrialEndsLabel,
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
