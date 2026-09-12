/* eslint-disable @typescript-eslint/no-explicit-any */
jest.mock("@salesos/hooks", () => ({
  registerCommand: jest.fn(),
}));

import { registerCommand } from "@salesos/hooks";
import { registerBuiltinCommands } from "../commands";

describe("registerBuiltinCommands", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it("registers all builtin commands", () => {
    const mockRouter = { push: jest.fn() } as any;
    registerBuiltinCommands(mockRouter);
    expect(registerCommand).toHaveBeenCalledTimes(10);
  });

  it("registers navigation commands with correct router pushes", () => {
    const mockRouter = { push: jest.fn() } as any;
    registerBuiltinCommands(mockRouter);

    const dashboardCall = (registerCommand as jest.Mock).mock.calls.find(
      (c: any) => c[0].id === "go.dashboard"
    );
    dashboardCall[0].handler();
    expect(mockRouter.push).toHaveBeenCalledWith("/v3");

    const companiesCall = (registerCommand as jest.Mock).mock.calls.find(
      (c: any) => c[0].id === "go.companies"
    );
    expect(companiesCall).toBeTruthy();
    companiesCall[0].handler();
    expect(mockRouter.push).toHaveBeenCalledWith("/v3/companies");
  });

  it("does not advertise pruned approvals or master-data destinations", () => {
    const mockRouter = { push: jest.fn() } as any;
    registerBuiltinCommands(mockRouter);

    const ids = (registerCommand as jest.Mock).mock.calls.map((c: any) => c[0].id);
    const pruned = [
      "go.v3.approvals",
      "go.v3.data",
      "go.v3.data.companies",
      "go.v3.data.people",
      "go.v3.data.er",
      "go.v3.data.review-queue",
      "go.data.companies",
      "go.data.people",
      "go.data.imports",
      "go.data.er",
    ];
    for (const id of pruned) {
      expect(ids).not.toContain(id);
    }

    expect(ids).toContain("go.v3.quotes");
    expect(ids).toContain("go.v3.contracts");
    expect(ids).toContain("go.admin");
  });

  it("does not advertise leftover GTM tip destinations", () => {
    const mockRouter = { push: jest.fn() } as any;
    registerBuiltinCommands(mockRouter);

    const ids = (registerCommand as jest.Mock).mock.calls.map((c: any) => c[0].id);
    const gtmTips = [
      "go.gtm",
      "go.gtm.icp",
      "go.gtm.market-sizing",
      "go.gtm.lead-discovery",
      "go.gtm.enrichment",
      "go.gtm.website-intelligence",
      "go.gtm.outreach",
      "go.gtm.verification",
      "go.gtm.lookalikes",
      "go.gtm.sequences",
    ];
    for (const id of gtmTips) {
      expect(ids).not.toContain(id);
    }
  });

  it("does not advertise leftover Tenant Studio or Marketplace tip destinations", () => {
    const mockRouter = { push: jest.fn() } as any;
    registerBuiltinCommands(mockRouter);

    const ids = (registerCommand as jest.Mock).mock.calls.map((c: any) => c[0].id);
    const studioMarketplaceTips = [
      "go.studio.custom-fields",
      "go.studio.scoring",
      "go.studio.permissions",
      "go.studio.workflows",
      "go.studio.notifications",
      "go.studio.branding",
      "go.studio.territories",
      "go.studio.ai-model-tiers",
      "go.studio.prompt-library",
      "go.studio.ai-policies",
      "go.studio.ai-memory",
      "go.marketplace.listings",
    ];
    for (const id of studioMarketplaceTips) {
      expect(ids).not.toContain(id);
    }

    expect(ids).toContain("go.admin");
  });

  it("does not advertise leftover Search hub destination", () => {
    const mockRouter = { push: jest.fn() } as any;
    registerBuiltinCommands(mockRouter);

    const ids = (registerCommand as jest.Mock).mock.calls.map((c: any) => c[0].id);
    expect(ids).not.toContain("go.search");
    expect(ids).toContain("action.search");
    expect(ids).toContain("go.admin");
  });

  it("does not advertise leftover Integrations Studio tip destinations", () => {
    const mockRouter = { push: jest.fn() } as any;
    registerBuiltinCommands(mockRouter);

    const ids = (registerCommand as jest.Mock).mock.calls.map((c: any) => c[0].id);
    const integrationsTips = [
      "go.integrations",
      "go.integrations.connect",
      "go.integrations.test",
      "go.integrations.map",
      "go.integrations.conflict",
      "go.integrations.schedule",
      "go.integrations.monitor",
      "go.integrations.disconnect",
    ];
    for (const id of integrationsTips) {
      expect(ids).not.toContain(id);
    }

    expect(ids).toContain("go.settings");
    expect(ids).toContain("go.admin");
  });

  it("retargets leftover go.settings to /v3/settings and leaves go.admin on /admin", () => {
    const mockRouter = { push: jest.fn() } as any;
    registerBuiltinCommands(mockRouter);

    const settingsCall = (registerCommand as jest.Mock).mock.calls.find(
      (c: any) => c[0].id === "go.settings"
    );
    expect(settingsCall).toBeTruthy();
    settingsCall[0].handler();
    expect(mockRouter.push).toHaveBeenCalledWith("/v3/settings");

    const adminCall = (registerCommand as jest.Mock).mock.calls.find(
      (c: any) => c[0].id === "go.admin"
    );
    expect(adminCall).toBeTruthy();
    adminCall[0].handler();
    expect(mockRouter.push).toHaveBeenCalledWith("/admin");
  });

  it("registers action commands that dispatch custom events", () => {
    const dispatchSpy = jest.spyOn(window, "dispatchEvent");
    const mockRouter = { push: jest.fn() } as any;
    registerBuiltinCommands(mockRouter);

    const copilotCall = (registerCommand as jest.Mock).mock.calls.find(
      (c: any) => c[0].id === "action.copilot"
    );
    copilotCall[0].handler();
    expect(dispatchSpy).toHaveBeenCalledWith(
      expect.objectContaining({ type: "salesos:toggle-copilot" })
    );
  });
});
