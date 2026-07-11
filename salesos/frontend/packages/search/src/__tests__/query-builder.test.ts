import { SearchQueryBuilder, queryToKey, isQueryEmpty } from '../query-builder'

describe('SearchQueryBuilder', () => {
  it('creates empty query', () => {
    const q = SearchQueryBuilder.create().build()
    expect(q.text).toBe('')
    expect(q.types).toBeUndefined()
  })

  it('builds with text', () => {
    const q = SearchQueryBuilder.create('test').build()
    expect(q.text).toBe('test')
  })

  it('withTypes adds entity types', () => {
    const q = SearchQueryBuilder.create('test').withTypes(['company', 'person']).build()
    expect(q.types).toEqual(['company', 'person'])
  })

  it('addType appends to existing types', () => {
    const q = SearchQueryBuilder.create('test').withTypes(['company']).addType('signal').build()
    expect(q.types).toEqual(['company', 'signal'])
  })

  it('withFilters adds filters', () => {
    const q = SearchQueryBuilder.create('test').withFilters([{ field: 'industry', operator: 'eq', value: 'energy' }]).build()
    expect(q.filters).toHaveLength(1)
    expect(q.filters![0].field).toBe('industry')
  })

  it('addFilter appends to existing filters', () => {
    const q = SearchQueryBuilder.create('test')
      .withFilters([{ field: 'industry', operator: 'eq', value: 'energy' }])
      .addFilter({ field: 'region', operator: 'eq', value: 'riyadh' })
      .build()
    expect(q.filters).toHaveLength(2)
  })

  it('withPage and withPageSize', () => {
    const q = SearchQueryBuilder.create('test').withPage(2).withPageSize(20).build()
    expect(q.page).toBe(2)
    expect(q.pageSize).toBe(20)
  })

  it('withSort', () => {
    const q = SearchQueryBuilder.create('test').withSort('recency').build()
    expect(q.sort).toBe('recency')
  })

  it('withScope', () => {
    const q = SearchQueryBuilder.create('test').withScope('company', 'c123').build()
    expect(q.scope).toEqual({ entityType: 'company', entityId: 'c123' })
  })

  it('withNaturalLanguage', () => {
    const q = SearchQueryBuilder.create('test').withNaturalLanguage(true).build()
    expect(q.naturalLanguage).toBe(true)
  })

  it('chains all methods', () => {
    const q = SearchQueryBuilder.create('energy companies')
      .withTypes(['company'])
      .addFilter({ field: 'industry', operator: 'eq', value: 'energy' })
      .withPage(1).withPageSize(10).withSort('relevance')
      .build()
    expect(q.text).toBe('energy companies')
    expect(q.types).toEqual(['company'])
    expect(q.page).toBe(1)
  })
})

describe('queryToKey', () => {
  it('generates key from text', () => {
    expect(queryToKey({ text: 'test' })).toBe('test')
  })

  it('includes types in key', () => {
    const key = queryToKey({ text: 'test', types: ['company'] })
    expect(key).toContain('types:company')
  })

  it('includes filters in key', () => {
    const key = queryToKey({ text: 'test', filters: [{ field: 'industry', operator: 'eq', value: 'energy' }] })
    expect(key).toContain('filters')
  })

  it('includes page and size', () => {
    const key = queryToKey({ text: 'test', page: 2, pageSize: 20 })
    expect(key).toContain('page:2')
    expect(key).toContain('size:20')
  })
})

describe('isQueryEmpty', () => {
  it('returns true for empty string', () => {
    expect(isQueryEmpty({ text: '' })).toBe(true)
  })

  it('returns true for whitespace', () => {
    expect(isQueryEmpty({ text: '   ' })).toBe(true)
  })

  it('returns false for valid text', () => {
    expect(isQueryEmpty({ text: 'test' })).toBe(false)
  })
})
