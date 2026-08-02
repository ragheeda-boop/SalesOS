/**
 * FE-S11-03b / FE-S11-06b — Tip-only GTM handoffs between tip GTM pages.
 * Query keys mirror tip HTTP / existing deep-link fields only.
 * Not Production GO / RAG GO. No territories / lookalike invent.
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

export type EnrichmentHandoff = {
  company_name?: string;
  domain?: string;
  run?: string;
};

export function buildEnrichmentHref(seed: EnrichmentHandoff = {}): string {
  const params = new URLSearchParams();
  if (seed.run?.trim()) params.set("run", seed.run.trim());
  if (seed.company_name?.trim())
    params.set("company_name", seed.company_name.trim());
  if (seed.domain?.trim()) params.set("domain", seed.domain.trim());
  const qs = params.toString();
  return qs ? `/gtm/enrichment?${qs}` : "/gtm/enrichment";
}

export type VerificationHandoff = {
  email?: string;
  phone?: string;
  run?: string;
};

export function buildVerificationHref(seed: VerificationHandoff = {}): string {
  const params = new URLSearchParams();
  if (seed.run?.trim()) params.set("run", seed.run.trim());
  if (seed.email?.trim()) params.set("email", seed.email.trim());
  if (seed.phone?.trim()) params.set("phone", seed.phone.trim());
  const qs = params.toString();
  return qs ? `/gtm/verification?${qs}` : "/gtm/verification";
}

export function buildIcpProfileHref(profileId?: string | null): string {
  if (profileId?.trim()) {
    return `/gtm/icp?profile=${encodeURIComponent(profileId.trim())}`;
  }
  return "/gtm/icp";
}

/** Pull tip enrichable contact fields from an enrichment filled map. */
export function contactFieldsFromFilled(
  filled: Record<string, unknown> | null | undefined,
): VerificationHandoff {
  if (!filled) return {};
  const email = filled.email == null ? "" : String(filled.email).trim();
  const phone = filled.phone == null ? "" : String(filled.phone).trim();
  return {
    email: email || undefined,
    phone: phone || undefined,
  };
}
