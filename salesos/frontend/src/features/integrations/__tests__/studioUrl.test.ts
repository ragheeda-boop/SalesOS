import { buildStudioSearchParams, parseStudioStep } from "../studioUrl";

describe("studioUrl — FE-S08-11", () => {
  it("parses known studio steps only", () => {
    expect(parseStudioStep("monitor")).toBe("monitor");
    expect(parseStudioStep("CONFLICT")).toBe("conflict");
    expect(parseStudioStep("nope")).toBeNull();
    expect(parseStudioStep(null)).toBeNull();
  });

  it("builds shareable query strings", () => {
    expect(
      buildStudioSearchParams({ step: "connect", connectionId: null }),
    ).toBe("");
    expect(
      buildStudioSearchParams({
        step: "monitor",
        connectionId: "c1",
      }),
    ).toBe("?step=monitor&connection=c1");
  });
});
