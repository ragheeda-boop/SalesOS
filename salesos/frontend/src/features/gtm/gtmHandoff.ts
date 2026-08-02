/**
 * FE-S11-03b — Tip-only GTM criteria handoff between market-sizing ↔ lead-discovery.
 * Query keys mirror tip HTTP filter fields only. Not Production GO / RAG GO.
 */

export type GtmCriteriaHandoff = {
  industries: string;
  cities: string;
  employees_min: string;
  employees_max: string;
  name?: string;
};

export function buildLeadDiscoveryHref(criteria: GtmCriteriaHandoff): string {
  const params = new URLSearchParams();
  if (criteria.name?.trim()) params.set("name", criteria.name.trim());
  if (criteria.industries.trim())
    params.set("industries", criteria.industries.trim());
  if (criteria.cities.trim()) params.set("cities", criteria.cities.trim());
  if (criteria.employees_min.trim())
    params.set("employees_min", criteria.employees_min.trim());
  if (criteria.employees_max.trim())
    params.set("employees_max", criteria.employees_max.trim());
  const qs = params.toString();
  return qs ? `/gtm/lead-discovery?${qs}` : "/gtm/lead-discovery";
}

export function parseGtmCriteriaFromSearch(
  search: URLSearchParams,
): GtmCriteriaHandoff {
  return {
    name: search.get("name") ?? "",
    industries: search.get("industries") ?? "",
    cities: search.get("cities") ?? "",
    employees_min: search.get("employees_min") ?? "",
    employees_max: search.get("employees_max") ?? "",
  };
}

export function buildMarketSizingHref(snapshotId?: string | null): string {
  if (snapshotId?.trim()) {
    return `/gtm/market-sizing?snapshot=${encodeURIComponent(snapshotId.trim())}`;
  }
  return "/gtm/market-sizing";
}

export function buildLeadDiscoveryRunHref(runId?: string | null): string {
  if (runId?.trim()) {
    return `/gtm/lead-discovery?run=${encodeURIComponent(runId.trim())}`;
  }
  return "/gtm/lead-discovery";
}
