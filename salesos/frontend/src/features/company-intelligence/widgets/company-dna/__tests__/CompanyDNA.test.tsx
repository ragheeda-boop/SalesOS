import { render, screen } from '@testing-library/react'
import { CompanyDNAView } from '../CompanyDNAView'
import { CompanyDNAWidget } from '../CompanyDNAContainer'
import { describeWidgetContract } from '@salesos/workspace/testing'
import type { CompanyDNAViewProps } from '../types'
import type { CompanyDNA } from '@/application/company-intelligence/company-intelligence.dto'

const sampleDNA: CompanyDNA = {
  industry: 'energy', businessModel: 'b2b', size: { employees: 15000, revenue: '1.2B', label: 'enterprise' },
  growthPattern: 'accelerating',
  buyingBehaviour: { score: 78, intent: 'high' },
  technologyProfile: { erp: 'sap', crm: 'salesforce', cloud: 'azure' },
  financialHealth: { score: 82, revenue: 1_200_000_000, growth: 12.5, trend: 'up' },
  governmentExposure: { level: 'high', contracts: 45 },
  expansionPotential: { score: 72, markets: ['UAE', 'Egypt'] },
  digitalPresence: { score: 68, website: 'active', social: 'active' },
  hiringTrend: { trend: 'growing', openings: 120 },
  procurementMaturity: { score: 65, level: 'managed' },
  relationshipStrength: { score: 70, connections: 15 },
  buyingIntent: { score: 82, confidence: 0.88 },
  riskLevel: { score: 25, level: 'low' },
  confidenceScore: 0.92,
  dataFreshness: { score: 90, updatedAt: '2026-07-10T11:00:00Z' },
  goldenRecordStatus: { status: 'clean', sources: 5 },
}

const defaultProps: CompanyDNAViewProps = { dna: sampleDNA }

function renderView(overrides?: Partial<CompanyDNAViewProps>) {
  return render(<CompanyDNAView {...defaultProps} {...overrides} />)
}

describeWidgetContract({
  name: 'CompanyDNA',
  defaultData: sampleDNA,
  config: {
    metadata: { id: 'companyDNA', title: 'الحمض النووي للشركة', permissions: ['company:dna:read'], featureFlag: { enabled: true } },
    render: ({ data }) => <CompanyDNAView dna={data} />,
  },
})

describe('CompanyDNAView', () => {
  it('renders industry badge', () => {
    renderView()
    expect(screen.getByText('energy')).toBeInTheDocument()
  })

  it('renders business model badge', () => {
    renderView()
    expect(screen.getByText('b2b')).toBeInTheDocument()
  })

  it('renders employee count', () => {
    renderView()
    expect(screen.getByText('15,000')).toBeInTheDocument()
  })

  it('renders financial health score', () => {
    renderView()
    const pcts = screen.getAllByText('82%')
    expect(pcts.length).toBeGreaterThanOrEqual(1)
  })

  it('renders buying intent score', () => {
    renderView()
    const pcts = screen.getAllByText('82%')
    expect(pcts.length).toBeGreaterThanOrEqual(1)
  })

  it('renders revenue', () => {
    renderView()
    expect(screen.getByText(/\$1\.2B/)).toBeInTheDocument()
  })

  it('renders confidence', () => {
    renderView()
    expect(screen.getByText(/%92/)).toBeInTheDocument()
  })

  it('shows empty state when no dna', () => {
    renderView({ dna: null })
    expect(screen.getByText('جاري تحليل الشركة')).toBeInTheDocument()
  })

  it('has role="region" with aria-label', () => {
    renderView()
    expect(screen.getByRole('region', { name: 'الحمض النووي للشركة' })).toBeInTheDocument()
  })

  it('has dark mode variant classes', () => {
    renderView()
    const container = document.querySelector('[class*="dark:"]')
    expect(container).toBeInTheDocument()
  })
})

describe('CompanyDNAWidget (SDK integration)', () => {
  it('is a valid widget component', () => {
    expect(CompanyDNAWidget).toBeDefined()
  })
})
