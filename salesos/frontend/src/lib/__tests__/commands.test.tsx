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
    expect(registerCommand).toHaveBeenCalledTimes(34);
  });

  it("registers navigation commands with correct router pushes", () => {
    const mockRouter = { push: jest.fn() } as any;
    registerBuiltinCommands(mockRouter);

    const dashboardCall = (registerCommand as jest.Mock).mock.calls.find(
      (c: any) => c[0].id === "go.dashboard",
    );
    dashboardCall[0].handler();
    expect(mockRouter.push).toHaveBeenCalledWith("/dashboard");

    const integrationsCall = (registerCommand as jest.Mock).mock.calls.find(
      (c: any) => c[0].id === "go.integrations",
    );
    expect(integrationsCall).toBeTruthy();
    integrationsCall[0].handler();
    expect(mockRouter.push).toHaveBeenCalledWith("/integrations");
    const monitorCall = (registerCommand as jest.Mock).mock.calls.find(
      (c: any) => c[0].id === "go.integrations.monitor",
    );
    expect(monitorCall).toBeTruthy();
    monitorCall[0].handler();
    expect(mockRouter.push).toHaveBeenCalledWith("/integrations?step=monitor");
    const conflictCall = (registerCommand as jest.Mock).mock.calls.find(
      (c: any) => c[0].id === "go.integrations.conflict",
    );
    expect(conflictCall).toBeTruthy();
    conflictCall[0].handler();
    expect(mockRouter.push).toHaveBeenCalledWith("/integrations?step=conflict");

    const studioWorkflows = (registerCommand as jest.Mock).mock.calls.find(
      (c: any) => c[0].id === "go.studio.workflows",
    );
    expect(studioWorkflows).toBeTruthy();
    studioWorkflows[0].handler();
    expect(mockRouter.push).toHaveBeenCalledWith("/studio/workflows");

    const studioNotifications = (registerCommand as jest.Mock).mock.calls.find(
      (c: any) => c[0].id === "go.studio.notifications",
    );
    expect(studioNotifications).toBeTruthy();
    studioNotifications[0].handler();
    expect(mockRouter.push).toHaveBeenCalledWith("/studio/notifications");

    const studioBranding = (registerCommand as jest.Mock).mock.calls.find(
      (c: any) => c[0].id === "go.studio.branding",
    );
    expect(studioBranding).toBeTruthy();
    studioBranding[0].handler();
    expect(mockRouter.push).toHaveBeenCalledWith("/studio/branding");

    const studioTerritories = (registerCommand as jest.Mock).mock.calls.find(
      (c: any) => c[0].id === "go.studio.territories",
    );
    expect(studioTerritories).toBeTruthy();
    studioTerritories[0].handler();
    expect(mockRouter.push).toHaveBeenCalledWith("/studio/territories");

    const studioAiTiers = (registerCommand as jest.Mock).mock.calls.find(
      (c: any) => c[0].id === "go.studio.ai-model-tiers",
    );
    expect(studioAiTiers).toBeTruthy();
    studioAiTiers[0].handler();
    expect(mockRouter.push).toHaveBeenCalledWith("/studio/ai-model-tiers");

    const marketplaceListings = (registerCommand as jest.Mock).mock.calls.find(
      (c: any) => c[0].id === "go.marketplace.listings",
    );
    expect(marketplaceListings).toBeTruthy();
    marketplaceListings[0].handler();
    expect(mockRouter.push).toHaveBeenCalledWith("/marketplace/listings");

    const gtmHub = (registerCommand as jest.Mock).mock.calls.find(
      (c: any) => c[0].id === "go.gtm",
    );
    expect(gtmHub).toBeTruthy();
    gtmHub[0].handler();
    expect(mockRouter.push).toHaveBeenCalledWith("/gtm");

    const gtmIcp = (registerCommand as jest.Mock).mock.calls.find(
      (c: any) => c[0].id === "go.gtm.icp",
    );
    expect(gtmIcp).toBeTruthy();
    gtmIcp[0].handler();
    expect(mockRouter.push).toHaveBeenCalledWith("/gtm/icp");

    const gtmMarketSizing = (registerCommand as jest.Mock).mock.calls.find(
      (c: any) => c[0].id === "go.gtm.market-sizing",
    );
    expect(gtmMarketSizing).toBeTruthy();
    gtmMarketSizing[0].handler();
    expect(mockRouter.push).toHaveBeenCalledWith("/gtm/market-sizing");

    const gtmLeadDiscovery = (registerCommand as jest.Mock).mock.calls.find(
      (c: any) => c[0].id === "go.gtm.lead-discovery",
    );
    expect(gtmLeadDiscovery).toBeTruthy();
    gtmLeadDiscovery[0].handler();
    expect(mockRouter.push).toHaveBeenCalledWith("/gtm/lead-discovery");

    const gtmEnrichment = (registerCommand as jest.Mock).mock.calls.find(
      (c: any) => c[0].id === "go.gtm.enrichment",
    );
    expect(gtmEnrichment).toBeTruthy();
    gtmEnrichment[0].handler();
    expect(mockRouter.push).toHaveBeenCalledWith("/gtm/enrichment");

    const gtmVerification = (registerCommand as jest.Mock).mock.calls.find(
      (c: any) => c[0].id === "go.gtm.verification",
    );
    expect(gtmVerification).toBeTruthy();
    gtmVerification[0].handler();
    expect(mockRouter.push).toHaveBeenCalledWith("/gtm/verification");

    const gtmLookalikes = (registerCommand as jest.Mock).mock.calls.find(
      (c: any) => c[0].id === "go.gtm.lookalikes",
    );
    expect(gtmLookalikes).toBeTruthy();
    gtmLookalikes[0].handler();
    expect(mockRouter.push).toHaveBeenCalledWith("/gtm/lookalikes");

    const gtmSequences = (registerCommand as jest.Mock).mock.calls.find(
      (c: any) => c[0].id === "go.gtm.sequences",
    );
    expect(gtmSequences).toBeTruthy();
    gtmSequences[0].handler();
    expect(mockRouter.push).toHaveBeenCalledWith("/gtm/sequences");
  });

  it("registers action commands that dispatch custom events", () => {
    const dispatchSpy = jest.spyOn(window, "dispatchEvent");
    const mockRouter = { push: jest.fn() } as any;
    registerBuiltinCommands(mockRouter);

    const copilotCall = (registerCommand as jest.Mock).mock.calls.find(
      (c: any) => c[0].id === "action.copilot",
    );
    copilotCall[0].handler();
    expect(dispatchSpy).toHaveBeenCalledWith(
      expect.objectContaining({ type: "salesos:toggle-copilot" }),
    );
  });
});
