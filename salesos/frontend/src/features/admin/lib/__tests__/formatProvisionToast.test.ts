import {
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
