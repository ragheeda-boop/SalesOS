export const companyKeys = {
  all: ["companies"] as const,
  lists: () => [...companyKeys.all, "list"] as const,
  list: (filters: Record<string, unknown>) => [...companyKeys.lists(), filters] as const,
  details: () => [...companyKeys.all, "detail"] as const,
  detail: (id: string) => [...companyKeys.details(), id] as const,
};

export const searchKeys = {
  all: ["search"] as const,
  results: (query: string, filters: Record<string, unknown>) =>
    [...searchKeys.all, query, filters] as const,
  suggestions: (query: string, field: string) =>
    [...searchKeys.all, "suggest", query, field] as const,
};

export const tenantKeys = {
  all: ["tenants"] as const,
  detail: (id: string) => [...tenantKeys.all, id] as const,
};

export const dashboardKeys = {
  stats: () => ["dashboard", "stats"] as const,
  exec: () => ["dashboard", "executive"] as const,
};

export const company360Keys = {
  detail: (id: string) => ["company360", id] as const,
};

export const employeeKeys = {
  all: ["employees"] as const,
  detail: (id: string) => [...employeeKeys.all, id] as const,
  me: () => [...employeeKeys.all, "me"] as const,
};

export const contactKeys = {
  all: ["contacts"] as const,
  lists: () => [...contactKeys.all, "list"] as const,
  list: (filters: Record<string, unknown>) => [...contactKeys.lists(), filters] as const,
  details: () => [...contactKeys.all, "detail"] as const,
  detail: (id: string) => [...contactKeys.details(), id] as const,
};

export const activityKeys = {
  entity: (entityType: string, entityId: string) =>
    ["activities", entityType, entityId] as const,
};

export const opportunityKeys = {
  all: ["opportunities"] as const,
  lists: () => [...opportunityKeys.all, "list"] as const,
  list: () => [...opportunityKeys.lists()] as const,
  details: () => [...opportunityKeys.all, "detail"] as const,
  detail: (id: string) => [...opportunityKeys.details(), id] as const,
};

export const pipelineKeys = {
  all: ["pipelines"] as const,
  lists: () => [...pipelineKeys.all, "list"] as const,
  list: () => [...pipelineKeys.lists()] as const,
};

export const adminKeys = {
  metrics: () => ["admin", "metrics"] as const,
  health: () => ["admin", "health"] as const,
  goldenRecords: (filters: Record<string, unknown>) => ["admin", "golden-records", filters] as const,
  conflicts: (filters: Record<string, unknown>) => ["admin", "conflicts", filters] as const,
  dlq: (filters: Record<string, unknown>) => ["admin", "dlq", filters] as const,
  dlqStats: () => ["admin", "dlq", "stats"] as const,
};
