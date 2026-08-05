import {
  buildEnrichmentHref,
  buildIcpProfileHref,
  buildLeadDiscoveryHref,
  buildLeadDiscoveryRunHref,
  buildLookalikeHref,
  buildMarketSizingHref,
  buildVerificationHref,
  contactFieldsFromFilled,
  parseGtmCriteriaFromSearch,
} from "../gtmHandoff";

describe("gtmHandoff — FE-S11-03b / FE-S11-06b", () => {
  it("builds lead-discovery href from tip criteria fields", () => {
    expect(
      buildLeadDiscoveryHref({
        name: "Pilot discovery",
        industries: "technology",
        cities: "riyadh",
        employees_min: "10",
        employees_max: "500",
      })
    ).toBe(
      "/gtm/lead-discovery?name=Pilot+discovery&industries=technology&cities=riyadh&employees_min=10&employees_max=500"
    );
  });

  it("parses tip criteria from search params", () => {
    const parsed = parseGtmCriteriaFromSearch(
      new URLSearchParams("industries=tech&cities=jeddah&employees_min=5&employees_max=50&name=X")
    );
    expect(parsed.industries).toBe("tech");
    expect(parsed.cities).toBe("jeddah");
    expect(parsed.employees_min).toBe("5");
    expect(parsed.name).toBe("X");
  });

  it("builds snapshot/run deep-links", () => {
    expect(buildMarketSizingHref("snap1")).toBe("/gtm/market-sizing?snapshot=snap1");
    expect(buildLeadDiscoveryRunHref("run1")).toBe("/gtm/lead-discovery?run=run1");
  });

  it("builds enrichment + verification + icp deep-links", () => {
    expect(
      buildEnrichmentHref({
        company_name: "Acme Pilot Co",
        domain: "acme.example",
      })
    ).toBe("/gtm/enrichment?company_name=Acme+Pilot+Co&domain=acme.example");
    expect(buildEnrichmentHref({ run: "enr1" })).toBe("/gtm/enrichment?run=enr1");
    expect(
      buildVerificationHref({
        email: "a@b.com",
        phone: "+9665",
      })
    ).toBe("/gtm/verification?email=a%40b.com&phone=%2B9665");
    expect(buildIcpProfileHref("icp1")).toBe("/gtm/icp?profile=icp1");
    expect(
      buildLookalikeHref({
        company_name: "Acme",
        industry: "technology",
        city: "riyadh",
      })
    ).toBe("/gtm/lookalikes?company_name=Acme&industry=technology&city=riyadh");
  });

  it("extracts tip contact fields from enrichment filled", () => {
    expect(
      contactFieldsFromFilled({
        email: "x@y.com",
        phone: "+1",
        industry: "tech",
      })
    ).toEqual({ email: "x@y.com", phone: "+1" });
    expect(contactFieldsFromFilled({})).toEqual({});
  });
});
