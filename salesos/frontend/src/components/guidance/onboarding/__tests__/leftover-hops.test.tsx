import { render } from "@testing-library/react";
import { OnboardingProvider, useOnboarding } from "../OnboardingProvider";

function hrefById(): Record<string, string> {
  let items: { id: string; href: string }[] = [];
  function Probe() {
    items = useOnboarding().items;
    return null;
  }
  render(
    <OnboardingProvider>
      <Probe />
    </OnboardingProvider>
  );
  return Object.fromEntries(items.map((item) => [item.id, item.href]));
}

describe("leftover OnboardingProvider golden-path hops", () => {
  it("retargets leftover /opportunities and /dashboard to v3", () => {
    const hrefs = hrefById();
    expect(hrefs.pipeline).toBe("/v3/crm");
    expect(hrefs.nba).toBe("/v3");
    expect(Object.values(hrefs)).not.toContain("/opportunities");
    expect(Object.values(hrefs)).not.toContain("/dashboard");
  });

  it("leaves leftover /settings and /admin hops alone", () => {
    const hrefs = hrefById();
    expect(hrefs.profile).toBe("/settings");
    expect(hrefs.integrations).toBe("/settings");
    expect(hrefs.team).toBe("/admin");
  });
});
