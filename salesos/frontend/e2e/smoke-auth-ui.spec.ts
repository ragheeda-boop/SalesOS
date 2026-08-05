/**
 * Wave 13 — authenticated UI smoke (light validated).
 * Expects E2E_USER_EMAIL / E2E_USER_PASSWORD (disposable @example.com).
 * Prefer: salesos/scripts/smoke-ui.ps1 (registers + runs this file on chromium).
 */
import {
  test,
  expect,
  type Page,
  type ConsoleMessage,
  type Request,
  type Response,
} from "@playwright/test";
import * as fs from "node:fs";
import * as path from "node:path";

const EMAIL = process.env.E2E_USER_EMAIL;
const PASSWORD = process.env.E2E_USER_PASSWORD;
const API_BASE = process.env.API_BASE_URL || "http://127.0.0.1:8000";
const REPORT_DIR =
  process.env.SMOKE_UI_REPORT_DIR || path.join(process.cwd(), "test-results", "smoke-ui");

type PageProbe = {
  path: string;
  ok: boolean;
  finalUrl: string;
  title: string;
  notes: string[];
  consoleErrors: string[];
  failedRequests: string[];
};

const PAGES = ["/dashboard", "/", "/companies", "/decisions", "/copilot"] as const;

function ensureReportDir() {
  fs.mkdirSync(REPORT_DIR, { recursive: true });
}

async function gotoRetry(page: Page, route: string, attempts = 4) {
  let lastErr: unknown;
  for (let i = 0; i < attempts; i++) {
    try {
      return await page.goto(route, { waitUntil: "domcontentloaded", timeout: 45_000 });
    } catch (e) {
      lastErr = e;
      await page.waitForTimeout(1500 * (i + 1));
    }
  }
  throw lastErr;
}

async function seedTokens(page: Page) {
  const res = await page.request.post(`${API_BASE}/api/v1/identity/login`, {
    data: { email: EMAIL, password: PASSWORD },
    timeout: 90_000,
  });
  expect(res.ok(), `API login HTTP ${res.status()}`).toBeTruthy();
  const body = await res.json();
  await gotoRetry(page, "/login");
  await page.evaluate(
    ({ access_token, refresh_token, tenant_id }) => {
      localStorage.setItem("access_token", access_token);
      if (refresh_token) localStorage.setItem("refresh_token", refresh_token);
      if (tenant_id) localStorage.setItem("tenant_id", String(tenant_id));
    },
    {
      access_token: body.access_token as string,
      refresh_token: (body.refresh_token as string) || "",
      tenant_id: body.tenant_id != null ? String(body.tenant_id) : "",
    }
  );
}

async function uiLogin(page: Page) {
  // Input labels are visual-only (no id/htmlFor) - do not use getByLabel.
  await gotoRetry(page, "/login");
  await expect(page.getByRole("heading", { name: /Sign In|Login|تسجيل/i })).toBeVisible({
    timeout: 20_000,
  });
  await page.locator('input[type="email"]').fill(EMAIL!);
  await page.locator('input[type="password"]').fill(PASSWORD!);
  await page.getByRole("button", { name: /Login|Sign in|دخول|تسجيل/i }).click();

  // Wait for token from UI login, or fall back to API token seed.
  try {
    await page.waitForFunction(() => !!localStorage.getItem("access_token"), null, {
      timeout: 25_000,
    });
  } catch {
    await seedTokens(page);
  }
  const token = await page.evaluate(() => localStorage.getItem("access_token"));
  expect(token, "access_token missing after UI/API login").toBeTruthy();
}

async function probePage(page: Page, route: string): Promise<PageProbe> {
  const consoleErrors: string[] = [];
  const failedRequests: string[] = [];
  const notes: string[] = [];

  const onConsole = (msg: ConsoleMessage) => {
    if (msg.type() === "error") consoleErrors.push(msg.text());
  };
  const onRequestFailed = (req: Request) => {
    failedRequests.push(`${req.failure()?.errorText || "failed"} ${req.method()} ${req.url()}`);
  };
  const onResponse = (res: Response) => {
    if (res.status() >= 400) {
      failedRequests.push(`HTTP ${res.status()} ${res.request().method()} ${res.url()}`);
    }
  };

  page.on("console", onConsole);
  page.on("requestfailed", onRequestFailed);
  page.on("response", onResponse);

  let ok = false;
  let finalUrl = "";
  let title = "";
  try {
    const resp = await gotoRetry(page, route);
    await page.waitForTimeout(1500);
    finalUrl = page.url();
    title = await page.title();
    const status = resp?.status() ?? 0;
    const bodyText = (
      await page
        .locator("body")
        .innerText()
        .catch(() => "")
    ).slice(0, 500);
    const redirectedToLogin = /\/login/.test(finalUrl);
    const looksBroken =
      status >= 500 ||
      /Application error|Internal Server Error|This page could not be found|404/i.test(bodyText);

    if (redirectedToLogin) {
      notes.push("redirected_to_login");
      ok = false;
    } else if (looksBroken) {
      notes.push(`broken_or_error status=${status}`);
      ok = false;
    } else {
      notes.push(`http=${status}`);
      ok = true;
    }

    const h1 = page.locator("h1").first();
    if (await h1.isVisible().catch(() => false)) {
      notes.push(`h1=${(await h1.innerText()).slice(0, 80)}`);
    } else {
      notes.push("no_h1");
    }
  } catch (e) {
    notes.push(`navigate_error=${e instanceof Error ? e.message : String(e)}`);
    ok = false;
    finalUrl = page.url();
  } finally {
    page.off("console", onConsole);
    page.off("requestfailed", onRequestFailed);
    page.off("response", onResponse);
  }

  return { path: route, ok, finalUrl, title, notes, consoleErrors, failedRequests };
}

test.describe("Wave 13 UI smoke (authenticated)", () => {
  test.skip(!EMAIL || !PASSWORD, "E2E_USER_EMAIL / E2E_USER_PASSWORD required");
  test.setTimeout(180_000);

  test("login + key pages (dashboard/home, companies, decisions, copilot)", async ({ page }) => {
    ensureReportDir();
    const results: PageProbe[] = [];

    await uiLogin(page);
    const afterLoginUrl = page.url();
    const hasToken = await page.evaluate(() => !!localStorage.getItem("access_token"));
    expect(hasToken, `No access_token after login (url=${afterLoginUrl})`).toBeTruthy();

    for (const route of PAGES) {
      results.push(await probePage(page, route));
    }

    const summary = {
      validation: "light validated",
      production_go: false,
      email: EMAIL,
      afterLoginUrl,
      pages: results.map((r) => ({
        path: r.path,
        ok: r.ok,
        finalUrl: r.finalUrl,
        title: r.title,
        notes: r.notes,
        consoleErrorCount: r.consoleErrors.length,
        failedRequestCount: r.failedRequests.length,
        consoleErrors: r.consoleErrors.slice(0, 20),
        failedRequests: r.failedRequests.slice(0, 30),
      })),
      passCount: results.filter((r) => r.ok).length,
      failCount: results.filter((r) => !r.ok).length,
    };

    const outPath = path.join(REPORT_DIR, "smoke-auth-ui-report.json");
    fs.writeFileSync(outPath, JSON.stringify(summary, null, 2), "utf8");
    // eslint-disable-next-line no-console
    console.log(`[smoke-ui] report written: ${outPath}`);
    // eslint-disable-next-line no-console
    console.log(`[smoke-ui] PASS=${summary.passCount} FAIL=${summary.failCount}`);

    // Hard fail only if login token missing (already asserted) or all pages broken.
    // Soft: companies + at least one of dashboard/home should open without login redirect.
    const companies = results.find((r) => r.path === "/companies");
    const homeish = results.filter((r) => r.path === "/dashboard" || r.path === "/");
    expect(companies?.ok, "companies page should open authenticated").toBeTruthy();
    expect(
      homeish.some((r) => r.ok),
      "dashboard or home should open authenticated"
    ).toBeTruthy();
  });
});
