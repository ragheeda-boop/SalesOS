import {
  activityStatusLabel,
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
      "tenant_id=t-1 · reason=Owner Console · provisioning=suspended",
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
