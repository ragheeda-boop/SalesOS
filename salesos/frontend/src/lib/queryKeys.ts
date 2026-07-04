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

export const activityKeys = {
  entity: (entityType: string, entityId: string) =>
    ["activities", entityType, entityId] as const,
};
