import { V3_CMD_EXTRA, V3_DOMAIN_NAV, isV3NavActive } from "../nav";

const MUST_KEEP = [
  "/v3",
  "/v3/companies",
  "/v3/contacts",
  "/v3/crm",
  "/v3/activities",
  "/v3/tasks",
  "/v3/quotes",
  "/v3/proposals",
  "/v3/reviews",
  "/v3/contracts",
  "/v3/icp",
  "/v3/settings",
];

const MUST_KEEP_IN_CMDK = [
  ...MUST_KEEP,
  "/v3/admin/ai-prompts",
  "/v3/admin/ai-policies",
  "/v3/admin/ai-memory",
  "/v3/admin/ai-model-tiers",
  "/v3/rag",
  "/v3/recommendations",
  "/v3/admin/ai-governance",
  "/v3/evidence",
];

const OFF_PRIMARY = [
  "/v3/people",
  "/v3/approvals",
  "/v3/analytics",
  "/v3/sales-dashboard",
  "/v3/my-day",
  "/v3/effectiveness",
  "/v3/cs",
  "/v3/admin",
  "/v3/data",
  "/v3/data/companies",
  "/v3/data/people",
  "/v3/data/imports",
  "/v3/data/er",
  "/v3/review-queue",
];

describe("V3_DOMAIN_NAV", () => {
  it("keeps ~12 MVP golden-path items in primary chrome", () => {
    expect(V3_DOMAIN_NAV).toHaveLength(12);
  });

  it("includes commercial create cluster and live ICP", () => {
    const hrefs = V3_DOMAIN_NAV.map((item) => item.href);
    expect(hrefs).toEqual(MUST_KEEP);
  });

  it("has no duplicate hrefs", () => {
    const hrefs = V3_DOMAIN_NAV.map((item) => item.href);
    expect(new Set(hrefs).size).toBe(hrefs.length);
  });

  it("drops Emp360 / HITL / MD / GTM extras from primary (pages stay)", () => {
    const hrefs = new Set(V3_DOMAIN_NAV.map((item) => item.href));
    for (const href of OFF_PRIMARY) {
      expect(hrefs.has(href)).toBe(false);
    }
  });

  it("does not advertise /v3/shell in primary or customer CmdK", () => {
    expect(V3_DOMAIN_NAV.some((item) => item.href === "/v3/shell")).toBe(false);
    expect(V3_CMD_EXTRA.some((item) => item.href === "/v3/shell")).toBe(false);
  });
});

describe("V3_CMD_EXTRA", () => {
  it("exposes only the approved knowledge and intelligence destinations", () => {
    expect(V3_CMD_EXTRA.map((item) => item.href)).toEqual(MUST_KEEP_IN_CMDK.slice(MUST_KEEP.length));
    const cmdk = [...V3_DOMAIN_NAV, ...V3_CMD_EXTRA].map((item) => item.href);
    expect(cmdk).toEqual(MUST_KEEP_IN_CMDK);
    expect(cmdk).not.toContain("/v3/shell");
  });
});

describe("isV3NavActive", () => {
  it("treats Home as exact /v3 only", () => {
    expect(isV3NavActive("/v3", "/v3")).toBe(true);
    expect(isV3NavActive("/v3/", "/v3")).toBe(true);
    expect(isV3NavActive("/v3/companies", "/v3")).toBe(false);
  });

  it("matches nested company 360 under Companies", () => {
    expect(isV3NavActive("/v3/companies/abc", "/v3/companies")).toBe(true);
    expect(isV3NavActive("/v3/contacts", "/v3/companies")).toBe(false);
  });
});
