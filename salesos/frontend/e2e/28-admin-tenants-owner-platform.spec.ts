import { test, expect } from "@playwright/test";

/**
 * FE-S04-08 — E2E hooks for Owner Platform tenant admin UI.
 * Smoke only: navigate + open create modal (no mutating create/suspend).
 * Skips without credentials (same pattern as 08-admin-panel).
 * Full Stage 7 provision mutate remains approval-gated.
 */
test.describe("FE-S04-08 Admin tenants Owner Platform hooks", () => {
  test.skip(
    !process.env.E2E_USER_PASSWORD || !process.env.E2E_USER_EMAIL,
    "Credentials env vars not set",
  );

  test.beforeEach(async ({ page }) => {
    await page.goto("/login");
    await page.getByLabel(/البريد|email/i).fill(process.env.E2E_USER_EMAIL!);
    await page
      .getByLabel(/كلمة المرور|password/i)
      .fill(process.env.E2E_USER_PASSWORD!);
    await page.getByRole("button", { name: /دخول|Sign in/i }).click();
    await page.waitForURL(/dashboard/, { timeout: 10_000 });
  });

  test("admin tenants page exposes Owner Platform hooks", async ({ page }) => {
    await page.goto("/admin/tenants");
    await page.waitForLoadState("networkidle");
    await expect(page).toHaveURL(/admin\/tenants/, { timeout: 8_000 });
    await expect(page.getByTestId("owner-console-shell")).toBeVisible({
      timeout: 8_000,
    });
    await expect(page.getByTestId("owner-console-nav-tenants")).toBeVisible();
    await expect(page.getByTestId("owner-console-nav-flags")).toBeVisible();
    await expect(page.getByTestId("owner-console-nav-config")).toBeVisible();
    await expect(page.getByTestId("owner-console-nav-audit")).toBeVisible();
    await expect(
      page.getByTestId("owner-console-audience-banner"),
    ).toBeVisible();
    await expect(page.getByTestId("owner-console-host-banner")).toBeVisible();
    await expect(page.getByTestId("admin-tenants-page")).toBeVisible({
      timeout: 8_000,
    });
    await expect(page.getByTestId("admin-tenants-new")).toBeVisible();

    await page.getByTestId("admin-tenants-new").click();
    await expect(page.getByTestId("admin-tenants-create-modal")).toBeVisible({
      timeout: 5_000,
    });
    await expect(page.getByTestId("admin-tenants-create-name")).toBeVisible();
    await expect(page.getByTestId("admin-tenants-create-slug")).toBeVisible();
    await expect(page.getByTestId("admin-tenants-create-submit")).toBeVisible();
  });

  test("admin tenants filters expose activity + provisioning hooks", async ({
    page,
  }) => {
    await page.goto("/admin/tenants");
    await page.waitForLoadState("networkidle");
    await expect(page.getByTestId("admin-tenants-status-filter")).toBeVisible({
      timeout: 8_000,
    });
    await expect(
      page.getByTestId("admin-tenants-provisioning-filter"),
    ).toBeVisible();
  });

  test("admin tenants expose region/residency filter hooks", async ({
    page,
  }) => {
    await page.goto("/admin/tenants");
    await page.waitForLoadState("networkidle");
    await expect(page.getByTestId("admin-tenants-region-filter")).toBeVisible({
      timeout: 8_000,
    });
    await expect(
      page.getByTestId("admin-tenants-residency-filter"),
    ).toBeVisible();
  });

  test("admin tenants expose trial filter hook", async ({ page }) => {
    await page.goto("/admin/tenants");
    await page.waitForLoadState("networkidle");
    await expect(page.getByTestId("admin-tenants-trial-filter")).toBeVisible({
      timeout: 8_000,
    });
  });

  test("admin tenants expose plan_id column hook when rows exist", async ({
    page,
  }) => {
    await page.goto("/admin/tenants");
    await page.waitForLoadState("networkidle");
    const planIdCell = page.getByTestId("admin-tenants-row-plan-id").first();
    const hasRow = await planIdCell.isVisible().catch(() => false);
    test.skip(!hasRow, "No tenant rows for plan_id column hook");
    await expect(planIdCell).toBeVisible();
  });

  test("admin tenants expose sort hook", async ({ page }) => {
    await page.goto("/admin/tenants");
    await page.waitForLoadState("networkidle");
    await expect(page.getByTestId("admin-tenants-sort")).toBeVisible({
      timeout: 8_000,
    });
  });

  test("admin tenants expose plan_id server filter hook", async ({ page }) => {
    await page.goto("/admin/tenants");
    await page.waitForLoadState("networkidle");
    await expect(page.getByTestId("admin-tenants-plan-id-filter")).toBeVisible({
      timeout: 8_000,
    });
  });

  test("admin tenants expose result count hook", async ({ page }) => {
    await page.goto("/admin/tenants");
    await page.waitForLoadState("networkidle");
    await expect(page.getByTestId("admin-tenants-result-count")).toBeVisible({
      timeout: 8_000,
    });
  });

  test("admin tenants expose copy filter URL + page size hooks", async ({
    page,
  }) => {
    await page.goto("/admin/tenants");
    await page.waitForLoadState("networkidle");
    await expect(page.getByTestId("admin-tenants-copy-filter-url")).toBeVisible(
      { timeout: 8_000 },
    );
    await expect(page.getByTestId("admin-tenants-page-size")).toBeVisible();
  });

  test("admin tenants row reprovision hook when failed/pending exists", async ({
    page,
  }) => {
    await page.goto("/admin/tenants");
    await page.waitForLoadState("networkidle");
    const btn = page.getByTestId("admin-tenants-row-reprovision").first();
    const has = await btn.isVisible().catch(() => false);
    test.skip(!has, "No failed/pending row for reprovision hook");
    await expect(btn).toBeVisible();
  });

  test("admin tenants detail lifecycle hooks open without mutate", async ({
    page,
  }) => {
    await page.goto("/admin/tenants");
    await page.waitForLoadState("networkidle");
    const detailBtn = page.getByTestId("admin-tenants-detail-open").first();
    const hasRow = await detailBtn.isVisible().catch(() => false);
    test.skip(!hasRow, "No tenant rows to open detail");
    await detailBtn.click();
    await expect(page.getByTestId("admin-tenants-status")).toBeVisible({
      timeout: 8_000,
    });
    await expect(
      page.getByTestId("admin-tenants-lifecycle-copy"),
    ).toBeVisible();
    await expect(page.getByTestId("admin-tenants-copy-ids")).toBeVisible();
    await expect(page.getByTestId("admin-tenants-detail-delete")).toBeVisible();
    // Activate reason shown when tenant inactive; suspend reason when active
    const activateReason = page.getByTestId("admin-tenants-activate-reason");
    const suspendReason = page.getByTestId("admin-tenants-suspend-reason");
    const hasActivate = await activateReason.isVisible().catch(() => false);
    const hasSuspend = await suspendReason.isVisible().catch(() => false);
    expect(hasActivate || hasSuspend).toBeTruthy();
    // Reprovision only when provisioning failed/pending — assert hook exists if shown
    const reprovision = page.getByTestId("admin-tenants-reprovision");
    const hasReprovision = await reprovision.isVisible().catch(() => false);
    if (hasReprovision) {
      await expect(
        page.getByTestId("admin-tenants-reprovision-submit"),
      ).toBeVisible();
    }
    await expect(page.getByTestId("admin-tenants-billing")).toBeVisible();
    await expect(page.getByTestId("admin-tenants-subscription")).toBeVisible();
    await expect(
      page.getByTestId("admin-tenants-billing-catalog"),
    ).toBeVisible();
    await expect(
      page.getByTestId("admin-tenants-checkout-create"),
    ).toBeVisible();
    await expect(page.getByTestId("admin-tenants-portal-open")).toBeVisible();
    await expect(
      page.getByTestId("admin-tenants-platform-invoices"),
    ).toBeVisible();
    await expect(page.getByTestId("admin-tenants-usage-meters")).toBeVisible();
    await expect(page.getByTestId("admin-tenants-plan-change")).toBeVisible();
    await expect(page.getByTestId("admin-tenants-plan-quote")).toBeVisible();
    await expect(page.getByTestId("admin-tenants-dunning")).toBeVisible();
  });

  test("admin tenants delete honesty + retention hooks without mutate", async ({
    page,
  }) => {
    await page.goto("/admin/tenants");
    await page.waitForLoadState("networkidle");
    const deleteBtn = page.getByTestId("admin-tenants-delete-open").first();
    const hasRow = await deleteBtn.isVisible().catch(() => false);
    test.skip(!hasRow, "No tenant rows to open delete modal");
    await deleteBtn.click();
    await expect(page.getByTestId("admin-tenants-delete-honesty")).toBeVisible({
      timeout: 5_000,
    });
    await page.getByTestId("admin-tenants-hard-delete-confirm").check();
    await expect(
      page.getByTestId("admin-tenants-retention-honesty"),
    ).toBeVisible();
    await expect(
      page.getByTestId("admin-tenants-force-immediate"),
    ).toBeVisible();
    await page.getByRole("button", { name: /Cancel/i }).click();
  });

  test("admin tenants delete modal opens without mutate", async ({ page }) => {
    await page.goto("/admin/tenants");
    await page.waitForLoadState("networkidle");
    const deleteBtn = page.getByTestId("admin-tenants-delete-open").first();
    const hasRow = await deleteBtn.isVisible().catch(() => false);
    test.skip(!hasRow, "No tenant rows to open delete modal");
    await deleteBtn.click();
    await expect(page.getByTestId("admin-tenants-delete-modal")).toBeVisible({
      timeout: 5_000,
    });
    await expect(
      page.getByTestId("admin-tenants-hard-delete-confirm"),
    ).toBeVisible();
    // Cancel — no soft/hard delete
    await page.getByRole("button", { name: /Cancel/i }).click();
    await expect(page.getByTestId("admin-tenants-delete-modal")).toBeHidden({
      timeout: 5_000,
    });
  });

  test("admin billing exposes Owner Console shell hooks", async ({ page }) => {
    await page.goto("/admin/billing");
    await page.waitForLoadState("networkidle");
    await expect(page).toHaveURL(/admin\/billing/, { timeout: 8_000 });
    await expect(page.getByTestId("owner-console-shell")).toBeVisible({
      timeout: 8_000,
    });
    await expect(page.getByTestId("owner-console-nav-billing")).toBeVisible();
    await expect(
      page.getByTestId("owner-console-readpath-honesty"),
    ).toBeVisible();
    await expect(page.getByTestId("admin-billing-page")).toBeVisible();
    await expect(page.getByTestId("admin-billing-overview-link")).toBeVisible();
    await expect(page.getByTestId("admin-billing-tenants-link")).toBeVisible();
  });

  test("admin integrations inventory exposes honesty stub hooks", async ({
    page,
  }) => {
    await page.goto("/admin/integrations");
    await page.waitForLoadState("networkidle");
    await expect(page.getByTestId("owner-console-shell")).toBeVisible({
      timeout: 8_000,
    });
    await expect(
      page.getByTestId("owner-console-nav-integrations"),
    ).toBeVisible();
    await expect(page.getByTestId("admin-integrations-page")).toBeVisible();
    await expect(
      page.getByTestId("owner-ops-integrations-honesty"),
    ).toBeVisible();
    await expect(page.getByTestId("integrations-studio-shell")).toBeVisible();
    await expect(
      page.getByTestId("integrations-studio-api-honesty"),
    ).toBeVisible();
    await expect(
      page.getByTestId("integrations-studio-tenant-link"),
    ).toHaveAttribute("href", "/integrations");
  });

  test("integrations studio page exposes Hub HTTP flow hooks", async ({
    page,
  }) => {
    await page.goto("/integrations");
    await page.waitForLoadState("networkidle");
    await expect(page.getByTestId("integrations-page")).toBeVisible({
      timeout: 8_000,
    });
    await expect(page.getByTestId("integrations-studio")).toBeVisible();
    await expect(
      page.getByTestId("integrations-studio-live-honesty"),
    ).toBeVisible();
    await expect(
      page.getByTestId("integrations-studio-step-connect"),
    ).toBeVisible();
    await expect(
      page.getByTestId("integrations-studio-connect-submit"),
    ).toBeVisible();
    await expect(
      page.getByTestId("integrations-studio-step-conflict"),
    ).toBeVisible();
    await page.getByTestId("integrations-studio-step-map").click();
    await expect(
      page.getByTestId("integrations-studio-map-load"),
    ).toBeVisible();
    await expect(
      page.getByTestId("integrations-studio-map-baseline"),
    ).toBeVisible();
    await page.goto("/integrations?step=monitor");
    await page.waitForLoadState("networkidle");
    await expect(
      page.getByTestId("integrations-studio-monitor-status-filter"),
    ).toBeVisible();
    await page.goto("/integrations?step=map");
    await page.waitForLoadState("networkidle");
    await expect(
      page.getByTestId("integrations-studio-model-preset-crm-lead"),
    ).toBeVisible();
  });

  test("admin flags/config/audit expose ops honesty hooks", async ({
    page,
  }) => {
    for (const [path, pageId, honestyId, navId] of [
      [
        "/admin/flags",
        "admin-flags-page",
        "owner-ops-flags-honesty",
        "owner-console-nav-flags",
      ],
      [
        "/admin/config",
        "admin-config-page",
        "owner-ops-config-honesty",
        "owner-console-nav-config",
      ],
      [
        "/admin/audit",
        "admin-audit-page",
        "owner-ops-audit-honesty",
        "owner-console-nav-audit",
      ],
    ] as const) {
      await page.goto(path);
      await page.waitForLoadState("networkidle");
      await expect(page.getByTestId("owner-console-shell")).toBeVisible({
        timeout: 8_000,
      });
      await expect(page.getByTestId(navId)).toBeVisible();
      await expect(page.getByTestId(pageId)).toBeVisible();
      await expect(page.getByTestId(honestyId)).toBeVisible();
    }
  });
});
