import {
  FLAG_ODOO_INTEGRATION,
  MUHIDE_TENANT_SLUG,
} from "@/features/integrations/odooIncrementalHonesty";

describe("FE-S09-07b Owner flags Odoo honesty", () => {
  it("reuses tip Grade-A Odoo flag key for Owner Console callout", () => {
    expect(FLAG_ODOO_INTEGRATION).toBe("feature_odoo_integration");
    expect(MUHIDE_TENANT_SLUG).toBe("muhide");
  });
});
