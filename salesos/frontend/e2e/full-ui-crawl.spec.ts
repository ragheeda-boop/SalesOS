/**
 * Wave 13 — Full UI crawl (light validated).
 * Credentials via env only: E2E_USER_EMAIL / E2E_USER_PASSWORD
 *   (or SMOKE_EMAIL / SMOKE_PASSWORD mapped by runner).
 * Prefer: salesos/scripts/full-ui-crawl.ps1
 * Does NOT claim Production GO. Does not hardcode passwords.
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

const EMAIL = process.env.E2E_USER_EMAIL || process.env.SMOKE_EMAIL;
const PASSWORD = process.env.E2E_USER_PASSWORD || process.env.SMOKE_PASSWORD;
const API_BASE = process.env.API_BASE_URL || "http://127.0.0.1:8000";
const REPORT_DIR =
  process.env.CRAWL_REPORT_DIR || path.join(process.cwd(), "test-results", "full-ui-crawl");
const SCREENSHOT_DIR = path.join(REPORT_DIR, "screenshots");
const MAX_CLICKS_PER_PAGE = Number(process.env.CRAWL_MAX_CLICKS || "8");
const SETTLE_MS = Number(process.env.CRAWL_SETTLE_MS || "1200");

/** Primary sidebar destinations (from dashboard layout NAV_KEYS, deduped). */
const NAV_ROUTES = [
  "/dashboard",
  "/companies",
  "/employees",
  "/employees/me",
  "/contacts",
  "/opportunities",
  "/activities",
  "/revenue",
  "/pipeline",
  "/forecast",
  "/search",
  "/decisions",
  "/meetings",
  "/rag",
  "/ai",
  "/graph",
  "/copilot",
  "/automation",
  "/analytics",
  "/signals",
  "/rules",
  "/monitoring",
  "/customer-success",
  "/settings",
  "/admin",
] as const;

/** Important deep links (app-router pages not always in sidebar). */
const DEEP_ROUTES = [
  "/",
  "/login",
  "/register",
  "/admin/flags",
  "/admin/config",
  "/admin/audit",
  "/admin/tenants",
  "/decisions/templates",
  "/revenue/territories",
  "/revenue/quotas",
  "/pipeline/analytics",
  "/analytics/sales",
  "/analytics/revenue",
  "/analytics/pipeline",
  "/analytics/employees",
  "/analytics/automation",
  "/analytics/reports/builder",
  "/automation/workflows/new",
  "/automation/analytics",
  "/search/analytics",
  "/knowledge",
  "/knowledge/connectors",
  "/marketplace",
  "/copilot/telemetry",
] as const;

type ClickResult = {
  label: string;
  kind: "button" | "tab" | "link";
  ok: boolean;
  note: string;
  urlBefore: string;
  urlAfter: string;
};

type PageResult = {
  path: string;
  category: "nav" | "deep" | "auth";
  ok: boolean;
  finalUrl: string;
  title: string;
  httpStatus: number | null;
  notes: string[];
  consoleErrors: string[];
  failedRequests: string[];
  http4xx5xx: string[];
  clicks: ClickResult[];
  screenshot?: string;
  emptyStateHint?: boolean;
  skippedClicks?: string[];
};

function ensureDirs() {
  fs.mkdirSync(REPORT_DIR, { recursive: true });
  fs.mkdirSync(SCREENSHOT_DIR, { recursive: true });
}

function safeName(route: string) {
  return route.replace(/[^\w.-]+/g, "_").replace(/^_/, "") || "root";
}

async function gotoRetry(page: Page, route: string, attempts = 3) {
  let lastErr: unknown;
  for (let i = 0; i < attempts; i++) {
    try {
      return await page.goto(route, { waitUntil: "domcontentloaded", timeout: 45_000 });
    } catch (e) {
      lastErr = e;
      await page.waitForTimeout(1000 * (i + 1));
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
  await gotoRetry(page, "/login");
  await expect(page.getByRole("heading", { name: /Sign In|Login|تسجيل/i })).toBeVisible({
    timeout: 20_000,
  });
  await page.locator('input[type="email"]').fill(EMAIL!);
  await page.locator('input[type="password"]').fill(PASSWORD!);
  await page.getByRole("button", { name: /Login|Sign in|دخول|تسجيل/i }).click();
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

function isExternalHref(href: string | null, baseOrigin: string): boolean {
  if (!href) return true;
  if (href.startsWith("mailto:") || href.startsWith("tel:") || href.startsWith("#")) return true;
  if (href.startsWith("http://") || href.startsWith("https://")) {
    try {
      return new URL(href).origin !== baseOrigin;
    } catch {
      return true;
    }
  }
  return false;
}

function shouldSkipClickLabel(label: string): string | null {
  const l = label.toLowerCase();
  if (/logout|sign out|log out|تسجيل الخروج|خروج/.test(l)) return "destructive_auth";
  if (/delete|remove|archive|destroy|حذف|أرشف/.test(l)) return "destructive";
  if (/download|export|import|upload|طباعة|تحميل/.test(l)) return "file_io";
  if (/external|open in|github|docs\.|documentation/.test(l)) return "likely_external";
  return null;
}

async function clickVisibleControls(
  page: Page,
  originPath: string
): Promise<{
  clicks: ClickResult[];
  skipped: string[];
}> {
  const clicks: ClickResult[] = [];
  const skipped: string[] = [];
  const baseOrigin = new URL(page.url()).origin;
  let remaining = MAX_CLICKS_PER_PAGE;

  // Tabs first (role=tab)
  const tabs = page.getByRole("tab");
  const tabCount = await tabs.count().catch(() => 0);
  for (let i = 0; i < tabCount && remaining > 0; i++) {
    const tab = tabs.nth(i);
    if (!(await tab.isVisible().catch(() => false))) continue;
    const label = ((await tab.innerText().catch(() => "")) || `tab-${i}`).trim().slice(0, 80);
    const skip = shouldSkipClickLabel(label);
    if (skip) {
      skipped.push(`${label} (${skip})`);
      continue;
    }
    const urlBefore = page.url();
    try {
      await tab.click({ timeout: 5_000 });
      await page.waitForTimeout(SETTLE_MS);
      clicks.push({
        label,
        kind: "tab",
        ok: true,
        note: "clicked",
        urlBefore,
        urlAfter: page.url(),
      });
      remaining--;
    } catch (e) {
      clicks.push({
        label,
        kind: "tab",
        ok: false,
        note: e instanceof Error ? e.message.slice(0, 120) : String(e),
        urlBefore,
        urlAfter: page.url(),
      });
      remaining--;
    }
  }

  // Primary buttons (visible, not in nav sidebar if possible)
  const buttons = page.locator(
    'main button:visible, [role="main"] button:visible, main a[role="button"]:visible'
  );
  const btnCount = Math.min(await buttons.count().catch(() => 0), 20);
  for (let i = 0; i < btnCount && remaining > 0; i++) {
    const btn = buttons.nth(i);
    if (!(await btn.isVisible().catch(() => false))) continue;
    if (!(await btn.isEnabled().catch(() => false))) {
      skipped.push(`disabled button #${i}`);
      continue;
    }
    const label = (
      (await btn.getAttribute("aria-label").catch(() => null)) ||
      (await btn.innerText().catch(() => "")) ||
      `button-${i}`
    )
      .trim()
      .replace(/\s+/g, " ")
      .slice(0, 80);
    if (!label || label.length < 1) continue;
    const skip = shouldSkipClickLabel(label);
    if (skip) {
      skipped.push(`${label} (${skip})`);
      continue;
    }
    // Avoid re-clicking same label
    if (clicks.some((c) => c.label === label && c.kind === "button")) continue;

    const urlBefore = page.url();
    try {
      await btn.click({ timeout: 5_000 });
      await page.waitForTimeout(SETTLE_MS);
      const urlAfter = page.url();
      // Dismiss simple dialogs / stay usable
      const dialog = page.getByRole("dialog");
      if (await dialog.isVisible().catch(() => false)) {
        const close = dialog
          .getByRole("button", { name: /close|cancel|إلغاء|إغلاق|dismiss/i })
          .first();
        if (await close.isVisible().catch(() => false)) {
          await close.click().catch(() => undefined);
          await page.waitForTimeout(400);
        } else {
          await page.keyboard.press("Escape").catch(() => undefined);
          await page.waitForTimeout(400);
        }
        skipped.push(`${label} (opened_modal_dismissed)`);
      }
      // If navigated away from origin family, go back for further clicks
      const leftOrigin =
        !new URL(urlAfter).pathname.startsWith(originPath.split("?")[0]) &&
        new URL(urlAfter).pathname !== originPath;
      clicks.push({
        label,
        kind: "button",
        ok: true,
        note: leftOrigin ? "navigated_away" : "clicked",
        urlBefore,
        urlAfter,
      });
      remaining--;
      if (leftOrigin && !/\/login/.test(urlAfter)) {
        await gotoRetry(page, originPath).catch(() => undefined);
        await page.waitForTimeout(SETTLE_MS);
      }
    } catch (e) {
      clicks.push({
        label,
        kind: "button",
        ok: false,
        note: e instanceof Error ? e.message.slice(0, 120) : String(e),
        urlBefore,
        urlAfter: page.url(),
      });
      remaining--;
      await gotoRetry(page, originPath).catch(() => undefined);
    }
  }

  // In-page links (main content only)
  const links = page.locator('main a[href]:visible, [role="main"] a[href]:visible');
  const linkCount = Math.min(await links.count().catch(() => 0), 15);
  for (let i = 0; i < linkCount && remaining > 0; i++) {
    const link = links.nth(i);
    if (!(await link.isVisible().catch(() => false))) continue;
    const href = await link.getAttribute("href").catch(() => null);
    if (isExternalHref(href, baseOrigin)) {
      skipped.push(`${href} (external_or_hash)`);
      continue;
    }
    const label = ((await link.innerText().catch(() => "")) || href || `link-${i}`)
      .trim()
      .replace(/\s+/g, " ")
      .slice(0, 80);
    const skip = shouldSkipClickLabel(label);
    if (skip) {
      skipped.push(`${label} (${skip})`);
      continue;
    }
    // Skip same-page and deep list pagination noise
    if (!href || href === "#" || href.startsWith("?")) {
      skipped.push(`${label} (query_or_hash)`);
      continue;
    }
    if (clicks.some((c) => c.label === label && c.kind === "link")) continue;

    const urlBefore = page.url();
    try {
      await link.click({ timeout: 5_000 });
      await page.waitForTimeout(SETTLE_MS);
      const urlAfter = page.url();
      clicks.push({
        label,
        kind: "link",
        ok: !/\/login/.test(urlAfter) || originPath === "/login",
        note: /\/login/.test(urlAfter) && originPath !== "/login" ? "auth_redirect" : "clicked",
        urlBefore,
        urlAfter,
      });
      remaining--;
      // Return to origin for more exploration
      if (new URL(urlAfter).pathname !== originPath.split("?")[0]) {
        await gotoRetry(page, originPath).catch(() => undefined);
        await page.waitForTimeout(SETTLE_MS);
      }
    } catch (e) {
      clicks.push({
        label,
        kind: "link",
        ok: false,
        note: e instanceof Error ? e.message.slice(0, 120) : String(e),
        urlBefore,
        urlAfter: page.url(),
      });
      remaining--;
      await gotoRetry(page, originPath).catch(() => undefined);
    }
  }

  return { clicks, skipped };
}

async function probePage(
  page: Page,
  route: string,
  category: PageResult["category"],
  interact: boolean
): Promise<PageResult> {
  const consoleErrors: string[] = [];
  const failedRequests: string[] = [];
  const http4xx5xx: string[] = [];
  const notes: string[] = [];

  const onConsole = (msg: ConsoleMessage) => {
    if (msg.type() === "error") {
      const t = msg.text();
      // Filter noisy Next.js RSC abort noise
      if (/Failed to load resource: the server responded with a status of 4/i.test(t)) {
        // still record briefly
      }
      consoleErrors.push(t.slice(0, 300));
    }
  };
  const onRequestFailed = (req: Request) => {
    const url = req.url();
    // Skip aborted prefetches
    const err = req.failure()?.errorText || "failed";
    if (/ERR_ABORTED/i.test(err) && /_rsc=/.test(url)) return;
    failedRequests.push(`${err} ${req.method()} ${url}`.slice(0, 300));
  };
  const onResponse = (res: Response) => {
    const status = res.status();
    if (status >= 400) {
      const url = res.url();
      // Ignore common static 404 favicons
      if (/favicon|hot-update|\.map(\?|$)/i.test(url)) return;
      http4xx5xx.push(`HTTP ${status} ${res.request().method()} ${url}`.slice(0, 300));
    }
  };

  page.on("console", onConsole);
  page.on("requestfailed", onRequestFailed);
  page.on("response", onResponse);

  let ok = false;
  let finalUrl = "";
  let title = "";
  let httpStatus: number | null = null;
  let clicks: ClickResult[] = [];
  let skippedClicks: string[] = [];
  let screenshot: string | undefined;
  let emptyStateHint = false;

  try {
    const resp = await gotoRetry(page, route);
    await page.waitForTimeout(SETTLE_MS);
    finalUrl = page.url();
    title = await page.title();
    httpStatus = resp?.status() ?? null;
    const bodyText = (
      await page
        .locator("body")
        .innerText()
        .catch(() => "")
    ).slice(0, 800);
    const redirectedToLogin =
      category !== "auth" && /\/login(\?|$)/.test(new URL(finalUrl).pathname);
    const looksBroken =
      (httpStatus != null && httpStatus >= 500) ||
      /Application error|Internal Server Error|This page could not be found/i.test(bodyText) ||
      (httpStatus === 404 && !bodyText);

    if (/no (data|results|items)|empty|nothing here|لا توجد|فارغ/i.test(bodyText)) {
      emptyStateHint = true;
      notes.push("empty_state_hint");
    }

    if (redirectedToLogin) {
      notes.push("redirected_to_login");
      ok = false;
    } else if (looksBroken) {
      notes.push(`broken_or_error status=${httpStatus}`);
      ok = false;
    } else if (httpStatus === 404) {
      notes.push("http_404");
      ok = false;
    } else {
      notes.push(`http=${httpStatus}`);
      ok = true;
    }

    const h1 = page.locator("h1").first();
    if (await h1.isVisible().catch(() => false)) {
      notes.push(`h1=${(await h1.innerText()).slice(0, 80).replace(/\s+/g, " ")}`);
    } else {
      notes.push("no_h1");
    }

    if (interact && ok && category !== "auth") {
      const result = await clickVisibleControls(page, route);
      clicks = result.clicks;
      skippedClicks = result.skipped.slice(0, 40);
      // Re-check page health after clicks
      finalUrl = page.url();
      if (/\/login(\?|$)/.test(new URL(finalUrl).pathname) && route !== "/login") {
        notes.push("post_click_auth_redirect");
        ok = false;
      }
    }

    if (!ok) {
      const shotPath = path.join(SCREENSHOT_DIR, `${safeName(route)}.png`);
      await page.screenshot({ path: shotPath, fullPage: true }).catch(() => undefined);
      if (fs.existsSync(shotPath)) {
        screenshot = shotPath;
        notes.push(`screenshot=${path.basename(shotPath)}`);
      }
    }
  } catch (e) {
    notes.push(`navigate_error=${e instanceof Error ? e.message.slice(0, 200) : String(e)}`);
    ok = false;
    finalUrl = page.url();
    const shotPath = path.join(SCREENSHOT_DIR, `${safeName(route)}-error.png`);
    await page.screenshot({ path: shotPath, fullPage: true }).catch(() => undefined);
    if (fs.existsSync(shotPath)) screenshot = shotPath;
  } finally {
    page.off("console", onConsole);
    page.off("requestfailed", onRequestFailed);
    page.off("response", onResponse);
  }

  return {
    path: route,
    category,
    ok,
    finalUrl,
    title,
    httpStatus,
    notes,
    consoleErrors: consoleErrors.slice(0, 25),
    failedRequests: failedRequests.slice(0, 25),
    http4xx5xx: http4xx5xx.slice(0, 40),
    clicks,
    screenshot,
    emptyStateHint,
    skippedClicks,
  };
}

test.describe("Wave 13 full UI crawl", () => {
  test.skip(!EMAIL || !PASSWORD, "E2E_USER_EMAIL / E2E_USER_PASSWORD (or SMOKE_*) required");
  test.setTimeout(900_000);

  test("login + crawl all nav + deep routes with primary clicks", async ({ page }) => {
    ensureDirs();
    const startedAt = new Date().toISOString();
    const results: PageResult[] = [];

    // Auth pages first (unauthenticated)
    results.push(await probePage(page, "/login", "auth", false));
    results.push(await probePage(page, "/register", "auth", false));

    await uiLogin(page);
    const afterLoginUrl = page.url();
    const hasToken = await page.evaluate(() => !!localStorage.getItem("access_token"));
    expect(hasToken, `No access_token after login (url=${afterLoginUrl})`).toBeTruthy();

    // Primary nav
    for (const route of NAV_ROUTES) {
      results.push(await probePage(page, route, "nav", true));
    }

    // Deep links (lighter interaction — still click tabs/buttons)
    for (const route of DEEP_ROUTES) {
      if (route === "/login" || route === "/register") continue;
      results.push(await probePage(page, route, "deep", true));
    }

    const passCount = results.filter((r) => r.ok).length;
    const failCount = results.filter((r) => !r.ok).length;
    const clicksAttempted = results.reduce((n, r) => n + r.clicks.length, 0);
    const clicksFailed = results.reduce((n, r) => n + r.clicks.filter((c) => !c.ok).length, 0);
    const pagesWithHttpErrors = results.filter((r) => r.http4xx5xx.length > 0).length;
    const pagesWithConsoleErrors = results.filter((r) => r.consoleErrors.length > 0).length;

    const uniqueRoutes = new Set(results.map((r) => r.path));
    const expectedMin = NAV_ROUTES.length + DEEP_ROUTES.length - 2; // login/register counted once in auth
    const coverageEstimatePct = Math.round((uniqueRoutes.size / Math.max(expectedMin, 1)) * 100);

    const critical = results
      .filter((r) => !r.ok)
      .map((r) => ({
        path: r.path,
        category: r.category,
        notes: r.notes,
        screenshot: r.screenshot ? path.basename(r.screenshot) : null,
        sampleHttp: r.http4xx5xx.slice(0, 5),
        sampleConsole: r.consoleErrors.slice(0, 3),
      }));

    const summary = {
      validation: "light validated",
      production_go: false,
      soak_untouched: true,
      startedAt,
      finishedAt: new Date().toISOString(),
      emailDomain: EMAIL!.includes("@") ? EMAIL!.split("@")[1] : "redacted",
      emailLocalPrefix: EMAIL!.split("@")[0]?.slice(0, 8) || "redacted",
      afterLoginUrl,
      baseUrl: process.env.BASE_URL || "http://127.0.0.1:3000",
      apiBase: API_BASE,
      maxClicksPerPage: MAX_CLICKS_PER_PAGE,
      pagesVisited: results.length,
      uniqueRoutes: uniqueRoutes.size,
      passCount,
      failCount,
      clicksAttempted,
      clicksFailed,
      pagesWithHttpErrors,
      pagesWithConsoleErrors,
      coverageEstimatePct,
      coverageNote:
        "Estimate = unique routes probed / (nav + deep catalog). Not every DOM click; modals/destructive/external skipped.",
      criticalFailures: critical,
      pages: results.map((r) => ({
        path: r.path,
        category: r.category,
        ok: r.ok,
        finalUrl: r.finalUrl,
        title: r.title,
        httpStatus: r.httpStatus,
        notes: r.notes,
        emptyStateHint: !!r.emptyStateHint,
        consoleErrorCount: r.consoleErrors.length,
        failedRequestCount: r.failedRequests.length,
        httpErrorCount: r.http4xx5xx.length,
        clickCount: r.clicks.length,
        clickFailCount: r.clicks.filter((c) => !c.ok).length,
        clicks: r.clicks,
        skippedClicks: r.skippedClicks?.slice(0, 20),
        consoleErrors: r.consoleErrors.slice(0, 10),
        http4xx5xx: r.http4xx5xx.slice(0, 15),
        failedRequests: r.failedRequests.slice(0, 10),
        screenshot: r.screenshot ? path.basename(r.screenshot) : null,
      })),
    };

    const outPath = path.join(REPORT_DIR, "full-ui-crawl-report.json");
    fs.writeFileSync(outPath, JSON.stringify(summary, null, 2), "utf8");

    // Compact markdown table for humans
    const mdLines = [
      "# Full UI Crawl — auto summary",
      "",
      `Generated: ${summary.finishedAt}`,
      `PASS=${passCount} FAIL=${failCount} clicks=${clicksAttempted} coverage~${coverageEstimatePct}%`,
      `Validation: light validated — NOT Production GO`,
      "",
      "| Route | Cat | Result | Notes |",
      "|-------|-----|--------|-------|",
      ...results.map((r) => {
        const st = r.ok ? "PASS" : "FAIL";
        const n = r.notes.join("; ").replace(/\|/g, "/");
        return `| \`${r.path}\` | ${r.category} | **${st}** | ${n.slice(0, 120)} |`;
      }),
      "",
    ];
    fs.writeFileSync(path.join(REPORT_DIR, "full-ui-crawl-summary.md"), mdLines.join("\n"), "utf8");

    // eslint-disable-next-line no-console
    console.log(`[full-ui-crawl] report: ${outPath}`);
    // eslint-disable-next-line no-console
    console.log(
      `[full-ui-crawl] PASS=${passCount} FAIL=${failCount} clicks=${clicksAttempted} coverage~${coverageEstimatePct}%`
    );

    // Soft gate: login worked + majority of nav pages open
    const navResults = results.filter((r) => r.category === "nav");
    const navPass = navResults.filter((r) => r.ok).length;
    expect(navPass, `nav pass ${navPass}/${navResults.length}`).toBeGreaterThanOrEqual(
      Math.ceil(navResults.length * 0.5)
    );
  });
});
