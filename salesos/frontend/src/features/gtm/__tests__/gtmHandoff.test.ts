import {
  buildLeadDiscoveryHref,
  buildLeadDiscoveryRunHref,
  buildMarketSizingHref,
  parseGtmCriteriaFromSearch,
} from "../gtmHandoff";

describe("gtmHandoff — FE-S11-03b", () => {
  it("builds lead-discovery href from tip criteria fields", () => {
    expect(
      buildLeadDiscoveryHref({
        name: "Pilot discovery",
        industries: "technology",
        cities: "riyadh",
        employees_min: "10",
        employees_max: "500",
      }),
    ).toBe(
      "/gtm/lead-discovery?name=Pilot+discovery&industries=technology&cities=riyadh&employees_min=10&employees_max=500",
    );
  });

  it("parses tip criteria from search params", () => {
    const parsed = parseGtmCriteriaFromSearch(
      new URLSearchParams(
        "industries=tech&cities=jeddah&employees_min=5&employees_max=50&name=X",
      ),
    );
    expect(parsed.industries).toBe("tech");
    expect(parsed.cities).toBe("jeddah");
    expect(parsed.employees_min).toBe("5");
    expect(parsed.name).toBe("X");
  });

  it("builds snapshot/run deep-links", () => {
    expect(buildMarketSizingHref("snap1")).toBe(
      "/gtm/market-sizing?snapshot=snap1",
    );
    expect(buildLeadDiscoveryRunHref("run1")).toBe(
      "/gtm/lead-discovery?run=run1",
    );
  });
});
