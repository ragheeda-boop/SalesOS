import { searchKeys } from '../search.keys'

describe('searchKeys', () => {
  it('all returns search', () => {
    expect(searchKeys.all).toEqual(['search'])
  })

  it('results includes query', () => {
    expect(searchKeys.results({ text: 'test' })).toEqual(['search', 'results', { text: 'test' }])
  })

  it('suggestions includes prefix', () => {
    expect(searchKeys.suggestions('acme')).toEqual(['search', 'suggestions', 'acme'])
  })

  it('ai includes query', () => {
    expect(searchKeys.ai('what is?')).toEqual(['search', 'ai', 'what is?'])
  })
})
