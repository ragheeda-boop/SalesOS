import {
  buildStudioSearchParams,
  parseRunModelFilter,
  parseRunStatusFilter,
  parseStudioStep,
} from "../studioUrl";

describe("studioUrl — FE-S08-11/12", () => {
  it("parses known steps and ignores unknown", () => {
    expect(parseStudioStep("monitor")).toBe("monitor");
    expect(parseStudioStep("nope")).toBeNull();
  });

  it("builds step and connection query", () => {
    expect(buildStudioSearchParams({ step: "map", connectionId: "c1" })).toBe(
      "?step=map&connection=c1",
    );
    expect(
      buildStudioSearchParams({ step: "connect", connectionId: null }),
    ).toBe("");
  });

  it("adds monitor runStatus/runModel filters when not all", () => {
    expect(parseRunStatusFilter("failed")).toBe("failed");
    expect(parseRunModelFilter("res.partner")).toBe("res.partner");
    expect(
      buildStudioSearchParams({
        step: "monitor",
        connectionId: "c1",
        runStatus: "failed",
        runModel: "crm.lead",
      }),
    ).toBe("?step=monitor&connection=c1&runStatus=failed&runModel=crm.lead");
    expect(
      buildStudioSearchParams({
        step: "monitor",
        connectionId: null,
        runStatus: "all",
        runModel: "all",
      }),
    ).toBe("?step=monitor");
  });
});
