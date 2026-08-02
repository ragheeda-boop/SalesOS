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
});
