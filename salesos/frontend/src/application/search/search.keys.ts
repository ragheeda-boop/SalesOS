export const searchKeys = {
  all: ['search'] as const,
  results: (query: unknown) => ['search', 'results', query] as const,
  suggestions: (prefix: string) => ['search', 'suggestions', prefix] as const,
  ai: (query: string) => ['search', 'ai', query] as const,
}
