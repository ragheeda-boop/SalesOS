import { searchApi, suggestApi } from '../search.api'

const mockFetch = jest.fn()
global.fetch = mockFetch

describe('searchApi', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('makes a POST request and returns JSON', async () => {
    const response = { results: [], total: 0 }
    mockFetch.mockResolvedValue({ ok: true, json: () => Promise.resolve(response) })

    const result = await searchApi({ text: 'test', filters: {}, page: 1, pageSize: 10 })

    expect(result).toEqual(response)
    expect(mockFetch).toHaveBeenCalledWith('/api/v1/search', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text: 'test', filters: {}, page: 1, pageSize: 10 }),
    })
  })

  it('throws on non-ok response', async () => {
    mockFetch.mockResolvedValue({ ok: false })

    await expect(searchApi({ text: 'test', filters: {}, page: 1, pageSize: 10 })).rejects.toThrow('Search failed')
  })
})

describe('suggestApi', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('returns suggestions', async () => {
    const suggestions = [{ id: '1', type: 'company', score: 0.9, data: { name: 'Acme' } }]
    mockFetch.mockResolvedValue({ ok: true, json: () => Promise.resolve(suggestions) })

    const result = await suggestApi('acme')

    expect(result).toEqual(suggestions)
    expect(mockFetch).toHaveBeenCalledWith('/api/v1/search/suggest', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ prefix: 'acme', limit: 5 }),
    })
  })

  it('returns empty array on failure', async () => {
    mockFetch.mockResolvedValue({ ok: false })

    const result = await suggestApi('acme')

    expect(result).toEqual([])
  })
})
