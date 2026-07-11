import type { SearchQuery, SearchFilter, SortOption, SearchEntityType } from './types'

export class SearchQueryBuilder {
  private query: SearchQuery

  constructor(text = '') {
    this.query = { text }
  }

  static create(text?: string) {
    return new SearchQueryBuilder(text ?? '')
  }

  withText(text: string): this {
    this.query.text = text
    return this
  }

  withTypes(types: SearchEntityType[]): this {
    this.query.types = types
    return this
  }

  addType(type: SearchEntityType): this {
    this.query.types = [...(this.query.types ?? []), type]
    return this
  }

  withFilters(filters: SearchFilter[]): this {
    this.query.filters = filters
    return this
  }

  addFilter(filter: SearchFilter): this {
    this.query.filters = [...(this.query.filters ?? []), filter]
    return this
  }

  withPage(page: number): this {
    this.query.page = page
    return this
  }

  withPageSize(size: number): this {
    this.query.pageSize = size
    return this
  }

  withSort(sort: SortOption): this {
    this.query.sort = sort
    return this
  }

  withScope(entityType: string, entityId: string): this {
    this.query.scope = { entityType, entityId }
    return this
  }

  withNaturalLanguage(enabled: boolean): this {
    this.query.naturalLanguage = enabled
    return this
  }

  build(): SearchQuery {
    return { ...this.query }
  }
}

export function queryToKey(query: SearchQuery): string {
  const parts = [query.text]
  if (query.types?.length) parts.push(`types:${query.types.join(',')}`)
  if (query.filters?.length) parts.push(`filters:${JSON.stringify(query.filters)}`)
  if (query.page) parts.push(`page:${query.page}`)
  if (query.pageSize) parts.push(`size:${query.pageSize}`)
  if (query.sort) parts.push(`sort:${query.sort}`)
  if (query.scope) parts.push(`scope:${query.scope.entityType}:${query.scope.entityId}`)
  return parts.join('|')
}

export function isQueryEmpty(query: SearchQuery): boolean {
  return !query.text || query.text.trim().length === 0
}

export function isQueryShort(query: SearchQuery): boolean {
  return query.text.trim().length < 2
}
