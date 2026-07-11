import { SearchHighlight, extractSnippets } from '../search-highlight'

describe('SearchHighlight component', () => {
  it('renders text without highlights', () => {
    const text = SearchHighlight({ text: 'Hello World', highlights: [] })
    expect(text).toBeDefined()
  })

  it('renders text with highlights', () => {
    const text = SearchHighlight({ text: 'Hello World', highlights: ['World'] })
    expect(text).toBeDefined()
  })
})

describe('extractSnippets', () => {
  it('extracts snippets around query match', () => {
    const snippets = extractSnippets('شركة أرامكو السعودية تعمل في قطاع الطاقة', 'أرامكو')
    expect(snippets.length).toBeGreaterThanOrEqual(1)
    expect(snippets[0]).toContain('أرامكو')
  })

  it('returns full text when no match', () => {
    const snippets = extractSnippets('Hello World', 'XYZ')
    expect(snippets[0]).toBe('Hello World')
  })
})
