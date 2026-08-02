export const companyKeys = {
  all: ["companies"] as const,
  lists: () => [...companyKeys.all, "list"] as const,
  list: (filters: Record<string, unknown>) =>
    [...companyKeys.lists(), filters] as const,
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
  lists: () => [...employeeKeys.all, "list"] as const,
  list: (filters: Record<string, unknown>) =>
    [...employeeKeys.lists(), filters] as const,
  details: () => [...employeeKeys.all, "detail"] as const,
  detail: (id: string) => [...employeeKeys.details(), id] as const,
  me: () => [...employeeKeys.all, "me"] as const,
  signals: (id: string) => [...employeeKeys.all, "signals", id] as const,
  score: (id: string) => [...employeeKeys.all, "score", id] as const,
  timeline: (id: string, params: Record<string, unknown>) =>
    [...employeeKeys.all, "timeline", id, params] as const,
  performance: (id: string) =>
    [...employeeKeys.all, "performance", id] as const,
  calendarKpis: (id: string) =>
    [...employeeKeys.all, "calendar-kpis", id] as const,
  calendarHeatmap: (id: string, days: number) =>
    [...employeeKeys.all, "calendar-heatmap", id, days] as const,
  emailKpis: (id: string, days: number) =>
    [...employeeKeys.all, "email-kpis", id, days] as const,
  emailTopContacts: (id: string) =>
    [...employeeKeys.all, "email-top-contacts", id] as const,
  emailDailyVolume: (id: string, days: number) =>
    [...employeeKeys.all, "email-daily-volume", id, days] as const,
  productivity: (id: string, periodDays: number) =>
    [...employeeKeys.all, "productivity", id, periodDays] as const,
  relationship: (id: string, targetType: string, targetId: string) =>
    [...employeeKeys.all, "relationship", id, targetType, targetId] as const,
  executiveSummary: () => [...employeeKeys.all, "executive-summary"] as const,
};

export const contactKeys = {
  all: ["contacts"] as const,
  lists: () => [...contactKeys.all, "list"] as const,
  list: (filters: Record<string, unknown>) =>
    [...contactKeys.lists(), filters] as const,
  details: () => [...contactKeys.all, "detail"] as const,
  detail: (id: string) => [...contactKeys.details(), id] as const,
};

export const activityKeys = {
  all: ["activities"] as const,
  global: (filters?: Record<string, unknown>) =>
    [...activityKeys.all, "global", filters] as const,
  entity: (entityType: string, entityId: string) =>
    ["activities", entityType, entityId] as const,
};

export const taskKeys = {
  all: ["tasks"] as const,
  lists: () => [...taskKeys.all, "list"] as const,
  list: (filters?: Record<string, unknown>) =>
    [...taskKeys.lists(), filters] as const,
  details: () => [...taskKeys.all, "detail"] as const,
  detail: (id: string) => [...taskKeys.details(), id] as const,
};

export const integrationHubKeys = {
  all: ["integration-hub"] as const,
  connections: (tenantId: string) =>
    [...integrationHubKeys.all, "connections", tenantId] as const,
  connection: (tenantId: string, connectionId: string) =>
    [...integrationHubKeys.all, "connection", tenantId, connectionId] as const,
  syncRuns: (tenantId: string, connectionId: string) =>
    [...integrationHubKeys.all, "sync-runs", tenantId, connectionId] as const,
  unlinkedBadges: (tenantId: string, connectionId: string) =>
    [
      ...integrationHubKeys.all,
      "unlinked-badges",
      tenantId,
      connectionId,
    ] as const,
  activeMapping: (tenantId: string, connectionId: string, model: string) =>
    [
      ...integrationHubKeys.all,
      "mapping",
      tenantId,
      connectionId,
      model,
    ] as const,
  conflictPolicy: (tenantId: string, connectionId: string) =>
    [
      ...integrationHubKeys.all,
      "conflict-policy",
      tenantId,
      connectionId,
    ] as const,
};

export const tenantStudioKeys = {
  all: ["tenant-studio"] as const,
  customFields: (tenantId: string, objectKey: string) =>
    [...tenantStudioKeys.all, "custom-fields", tenantId, objectKey] as const,
  formSchema: (tenantId: string, objectKey: string) =>
    [...tenantStudioKeys.all, "form-schema", tenantId, objectKey] as const,
  scoringRules: (tenantId: string) =>
    [...tenantStudioKeys.all, "scoring-rules", tenantId] as const,
  permissionsCatalog: (tenantId: string) =>
    [...tenantStudioKeys.all, "permissions-catalog", tenantId] as const,
  permissionsCeiling: (tenantId: string) =>
    [...tenantStudioKeys.all, "permissions-ceiling", tenantId] as const,
  customRoles: (tenantId: string) =>
    [...tenantStudioKeys.all, "custom-roles", tenantId] as const,
  workflows: (tenantId: string) =>
    [...tenantStudioKeys.all, "workflows", tenantId] as const,
  notificationRules: (tenantId: string) =>
    [...tenantStudioKeys.all, "notification-rules", tenantId] as const,
  notificationEvents: (tenantId: string) =>
    [...tenantStudioKeys.all, "notification-events", tenantId] as const,
  branding: (tenantId: string) =>
    [...tenantStudioKeys.all, "branding", tenantId] as const,
};

export const gtmKeys = {
  all: ["gtm"] as const,
  marketSizingMeta: (tenantId: string) =>
    [...gtmKeys.all, "market-sizing-meta", tenantId] as const,
  marketSizingList: (tenantId: string) =>
    [...gtmKeys.all, "market-sizing", tenantId] as const,
  marketSizingDetail: (tenantId: string, id: string) =>
    [...gtmKeys.all, "market-sizing", tenantId, id] as const,
  leadDiscoveryMeta: (tenantId: string) =>
    [...gtmKeys.all, "lead-discovery-meta", tenantId] as const,
  leadDiscoveryList: (tenantId: string) =>
    [...gtmKeys.all, "lead-discovery", tenantId] as const,
  leadDiscoveryDetail: (tenantId: string, id: string) =>
    [...gtmKeys.all, "lead-discovery", tenantId, id] as const,
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
  goldenRecords: (filters: Record<string, unknown>) =>
    ["admin", "golden-records", filters] as const,
  conflicts: (filters: Record<string, unknown>) =>
    ["admin", "conflicts", filters] as const,
  dlq: (filters: Record<string, unknown>) => ["admin", "dlq", filters] as const,
  dlqStats: () => ["admin", "dlq", "stats"] as const,
  tenants: (filters?: Record<string, unknown>) =>
    ["admin", "tenants", filters] as const,
  tenantDetail: (id: string) => ["admin", "tenants", id] as const,
  tenantUsage: (id: string) => ["admin", "tenants", id, "usage"] as const,
  plans: () => ["admin", "plans"] as const,
  licenses: () => ["admin", "licenses"] as const,
  users: (filters?: Record<string, unknown>) =>
    ["admin", "users", filters] as const,
  userDetail: (id: string) => ["admin", "users", id] as const,
  tenantSubscription: (tenantId: string) =>
    ["admin", "billing", "subscription", tenantId] as const,
  billingCatalog: (activeOnly?: boolean) =>
    ["admin", "billing", "catalog", activeOnly] as const,
  stripeStatus: () => ["admin", "billing", "stripe-status"] as const,
  platformInvoices: (tenantId?: string) =>
    ["admin", "billing", "platform-invoices", tenantId] as const,
  usageMeters: (filters?: Record<string, unknown>) =>
    ["admin", "billing", "usage", filters] as const,
  dunningCases: (filters?: Record<string, unknown>) =>
    ["admin", "billing", "dunning", filters] as const,
  invoices: (tenantId?: string) =>
    ["admin", "billing", "invoices", tenantId] as const,
  transactions: (tenantId?: string) =>
    ["admin", "billing", "transactions", tenantId] as const,
  featureFlags: () => ["admin", "feature-flags"] as const,
  featureFlagTenants: (id: string) =>
    ["admin", "feature-flags", id, "tenants"] as const,
  jobs: (filters?: Record<string, unknown>) =>
    ["admin", "jobs", filters] as const,
  jobDetail: (id: string) => ["admin", "jobs", id] as const,
  aiCosts: (filters?: Record<string, unknown>) =>
    ["admin", "ai", "costs", filters] as const,
  aiSummary: () => ["admin", "ai", "summary"] as const,
  aiUsage: () => ["admin", "ai", "usage"] as const,
  healthDetailed: () => ["admin", "health", "detailed"] as const,
  healthHistory: () => ["admin", "health", "history"] as const,
  roles: () => ["admin", "roles"] as const,
  permissions: () => ["admin", "permissions"] as const,
  auditLogs: (filters?: Record<string, unknown>) =>
    ["admin", "audit", "logs", filters] as const,
  config: () => ["admin", "config"] as const,
  configVersions: () => ["admin", "config", "versions"] as const,
};

export const ruleKeys = {
  all: ["rules"] as const,
  lists: () => [...ruleKeys.all, "list"] as const,
  list: (filters?: Record<string, unknown>) =>
    [...ruleKeys.lists(), filters] as const,
  details: () => [...ruleKeys.all, "detail"] as const,
  detail: (id: string) => [...ruleKeys.details(), id] as const,
};

export const settingsKeys = {
  all: ["settings"] as const,
  notifications: () => [...settingsKeys.all, "notifications"] as const,
  apiKeys: () => [...settingsKeys.all, "api-keys"] as const,
};

export const decisionKeys = {
  all: ["decisions"] as const,
  evaluate: () => [...decisionKeys.all, "evaluate"] as const,
  explain: (id: string) => [...decisionKeys.all, "explain", id] as const,
  history: (tenantId: string) =>
    [...decisionKeys.all, "history", tenantId] as const,
  recommendations: (entityId?: string) =>
    [...decisionKeys.all, "recommendations", entityId] as const,
  scores: (entityId: string) =>
    [...decisionKeys.all, "scores", entityId] as const,
  evidence: (entityId: string) =>
    [...decisionKeys.all, "evidence", entityId] as const,
  feedback: (tenantId: string) =>
    [...decisionKeys.all, "feedback", tenantId] as const,
};
