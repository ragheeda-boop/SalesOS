import {
  CURSOR_STATE_HONESTY,
  SYNCRUN_CURSOR_HONESTY,
  FLAG_ODOO_INTEGRATION,
  MUHIDE_TENANT_SLUG,
  ODOO_FLAG_GATED_ACTIONS,
  isOdooConnectorKey,
} from "../odooIncrementalHonesty";

describe("odooIncrementalHonesty — FE-S09-07", () => {
  it("mirrors tip feature_odoo_integration flag key", () => {
    expect(FLAG_ODOO_INTEGRATION).toBe("feature_odoo_integration");
    expect(MUHIDE_TENANT_SLUG).toBe("muhide");
    expect(ODOO_FLAG_GATED_ACTIONS).toEqual(
      expect.arrayContaining(["connect", "test_connection", "schedule"])
    );
  });

  it("documents tip cursor_state write_date honesty (no SyncRun cursor invent)", () => {
    expect(isOdooConnectorKey("odoo")).toBe(true);
    expect(isOdooConnectorKey("fake")).toBe(false);
    expect(CURSOR_STATE_HONESTY).toMatch(/write_date/);
    expect(SYNCRUN_CURSOR_HONESTY).toMatch(/cursor_before/);
    expect(SYNCRUN_CURSOR_HONESTY).toMatch(/sync-runs/);
  });
});
