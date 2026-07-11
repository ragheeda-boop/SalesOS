export const companyIntelligenceKeys = {
  all: ['company-intelligence'] as const,
  detail: (id: string) => ['company-intelligence', id] as const,
}
