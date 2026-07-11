import { buildFilterQuery, parseFilterString, toggleFacet, removeFacet, applyFacet } from '../search-filters'

describe('buildFilterQuery', () => {
  it('builds eq filter', () => {
    expect(buildFilterQuery([{ field: 'industry', operator: 'eq', value: 'energy' }])).toBe('industry:energy')
  })

  it('builds neq filter', () => {
    expect(buildFilterQuery([{ field: 'industry', operator: 'neq', value: 'energy' }])).toBe('-industry:energy')
  })

  it('builds gt/gte/lt/lte filters', () => {
    expect(buildFilterQuery([{ field: 'revenue', operator: 'gt', value: '1000000' }])).toBe('revenue>1000000')
    expect(buildFilterQuery([{ field: 'revenue', operator: 'gte', value: '1000000' }])).toBe('revenue>=1000000')
  })

  it('builds in filter', () => {
    expect(buildFilterQuery([{ field: 'region', operator: 'in', value: ['riyadh', 'jeddah'] }])).toBe('region:(riyadh,jeddah)')
  })

  it('handles empty filters', () => {
    expect(buildFilterQuery([])).toBe('')
  })
})

describe('parseFilterString', () => {
  it('parses eq filter', () => {
    const filters = parseFilterString('industry:energy')
    expect(filters).toHaveLength(1)
    expect(filters[0].field).toBe('industry')
    expect(filters[0].operator).toBe('eq')
  })

  it('parses neq filter', () => {
    const filters = parseFilterString('-industry:energy')
    expect(filters[0].operator).toBe('neq')
  })

  it('handles empty string', () => {
    expect(parseFilterString('')).toEqual([])
  })
})

describe('toggleFacet', () => {
  it('adds facet when not selected', () => {
    const filters = toggleFacet([], 'industry', 'energy')
    expect(filters).toHaveLength(1)
  })

  it('removes facet when already selected', () => {
    const filters = toggleFacet([{ field: 'industry', operator: 'eq', value: 'energy' }], 'industry', 'energy')
    expect(filters).toHaveLength(0)
  })
})

describe('removeFacet', () => {
  it('removes all filters for a field', () => {
    const filters = removeFacet([{ field: 'industry', operator: 'eq', value: 'energy' }], 'industry')
    expect(filters).toHaveLength(0)
  })
})
