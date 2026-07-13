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
  main: () => ["dashboard", "main"] as const,
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

export const taskKeys = {
  all: ["tasks"] as const,
  lists: () => [...taskKeys.all, "list"] as const,
  list: (filters?: Record<string, unknown>) => [...taskKeys.lists(), filters] as const,
  details: () => [...taskKeys.all, "detail"] as const,
  detail: (id: string) => [...taskKeys.details(), id] as const,
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
  tenants: (filters?: Record<string, unknown>) => ["admin", "tenants", filters] as const,
  tenantDetail: (id: string) => ["admin", "tenants", id] as const,
  tenantUsage: (id: string) => ["admin", "tenants", id, "usage"] as const,
  plans: () => ["admin", "plans"] as const,
  licenses: () => ["admin", "licenses"] as const,
  users: (filters?: Record<string, unknown>) => ["admin", "users", filters] as const,
  userDetail: (id: string) => ["admin", "users", id] as const,
  invoices: (tenantId?: string) => ["admin", "billing", "invoices", tenantId] as const,
  transactions: (tenantId?: string) => ["admin", "billing", "transactions", tenantId] as const,
  featureFlags: () => ["admin", "feature-flags"] as const,
  featureFlagTenants: (id: string) => ["admin", "feature-flags", id, "tenants"] as const,
  jobs: (filters?: Record<string, unknown>) => ["admin", "jobs", filters] as const,
  jobDetail: (id: string) => ["admin", "jobs", id] as const,
  aiCosts: (filters?: Record<string, unknown>) => ["admin", "ai", "costs", filters] as const,
  aiSummary: () => ["admin", "ai", "summary"] as const,
  aiUsage: () => ["admin", "ai", "usage"] as const,
  healthDetailed: () => ["admin", "health", "detailed"] as const,
  healthHistory: () => ["admin", "health", "history"] as const,
  roles: () => ["admin", "roles"] as const,
  permissions: () => ["admin", "permissions"] as const,
  auditLogs: (filters?: Record<string, unknown>) => ["admin", "audit", "logs", filters] as const,
};

export const decisionKeys = {
  all: ["decisions"] as const,
  evaluate: () => [...decisionKeys.all, "evaluate"] as const,
  explain: (id: string) => [...decisionKeys.all, "explain", id] as const,
  history: (tenantId: string) => [...decisionKeys.all, "history", tenantId] as const,
  recommendations: (entityId?: string) => [...decisionKeys.all, "recommendations", entityId] as const,
  scores: (entityId: string) => [...decisionKeys.all, "scores", entityId] as const,
  evidence: (entityId: string) => [...decisionKeys.all, "evidence", entityId] as const,
  feedback: (tenantId: string) => [...decisionKeys.all, "feedback", tenantId] as const,
};
