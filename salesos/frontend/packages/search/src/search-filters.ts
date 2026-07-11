import type { SearchFilter, SearchFacet, SearchQuery } from './types'

export function buildFilterQuery(filters: SearchFilter[]): string {
  return filters
    .map((f) => {
      switch (f.operator) {
        case 'eq': return `${f.field}:${f.value}`
        case 'neq': return `-${f.field}:${f.value}`
        case 'gt': return `${f.field}>${f.value}`
        case 'gte': return `${f.field}>=${f.value}`
        case 'lt': return `${f.field}<${f.value}`
        case 'lte': return `${f.field}<=${f.value}`
        case 'in': return `${f.field}:(${(f.value as string[]).join(',')})`
        case 'between': {
          const [a, b] = f.value as [unknown, unknown]
          return `${f.field}:${a}-${b}`
        }
        case 'contains': return `${f.field}:~${f.value}`
        default: return ''
      }
    })
    .filter(Boolean)
    .join(' ')
}

export function parseFilterString(filterStr: string): SearchFilter[] {
  if (!filterStr.trim()) return []
  return filterStr.split(' ').filter(Boolean).map((part) => {
    if (part.startsWith('-')) {
      const [field, value] = part.slice(1).split(':')
      return { field, operator: 'neq' as const, value }
    }
    if (part.includes('>=')) {
      const [field, value] = part.split('>=')
      return { field, operator: 'gte' as const, value }
    }
    if (part.includes('<=')) {
      const [field, value] = part.split('<=')
      return { field, operator: 'lte' as const, value }
    }
    if (part.includes('>')) {
      const [field, value] = part.split('>')
      return { field, operator: 'gt' as const, value }
    }
    if (part.includes('<')) {
      const [field, value] = part.split('<')
      return { field, operator: 'lt' as const, value }
    }
    if (part.includes(':(')) {
      const [field, rest] = part.split(':(')
      const values = rest.slice(0, -1).split(',')
      return { field, operator: 'in' as const, value: values }
    }
    if (part.includes(':') && part.includes('-') && !part.includes('~')) {
      const [field, rest] = part.split(':')
      const [a, b] = rest.split('-')
      return { field, operator: 'between' as const, value: [a, b] }
    }
    const [field, value] = part.split(':')
    return { field, operator: 'eq' as const, value }
  })
}

export function applyFacet(facets: SearchFacet[], field: string, value: string): SearchFilter[] {
  return [{ field, operator: 'eq', value }]
}

export function removeFacet(filters: SearchFilter[], field: string): SearchFilter[] {
  return filters.filter((f) => f.field !== field)
}

export function toggleFacet(filters: SearchFilter[], field: string, value: string): SearchFilter[] {
  const existing = filters.find((f) => f.field === field && f.value === value && f.operator === 'eq')
  if (existing) return filters.filter((f) => f !== existing)
  return [...filters, { field, operator: 'eq', value }]
}
