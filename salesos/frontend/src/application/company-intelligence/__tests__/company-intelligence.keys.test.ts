import { companyIntelligenceKeys } from '../company-intelligence.keys'

describe('companyIntelligenceKeys', () => {
  it('all returns company-intelligence', () => {
    expect(companyIntelligenceKeys.all).toEqual(['company-intelligence'])
  })

  it('detail includes company id', () => {
    expect(companyIntelligenceKeys.detail('c-1')).toEqual(['company-intelligence', 'c-1'])
  })
})
