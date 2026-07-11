import { render, screen } from '@testing-library/react'
import { TerritoryView } from '../TerritoryView'
import { TerritoryIntelligenceWidget } from '../TerritoryContainer'
import { describeWidgetContract } from '@salesos/workspace/testing'
import type { TerritoryData } from '../types'

const sample: TerritoryData = { territories: [{ id: 't1', name: 'الرياض', deals: 8, value: 3500000, quota: 4000000, attainment: 88 }], coverage: [], gaps: [{ region: 'القصيم', potentialValue: 1800000, reason: 'لا يوجد' }] }

function renderView(d: TerritoryData = sample) { return render(<TerritoryView data={d} />) }

describeWidgetContract({ name: 'TerritoryIntelligence', defaultData: sample, config: { metadata: { id: 'territoryIntelligence', title: 'ذكاء المناطق', permissions: ['territory:read'], featureFlag: { enabled: true } }, render: ({ data }) => <TerritoryView data={data} /> } })

describe('TerritoryView', () => {
  it('renders territory names', () => { renderView(); expect(screen.getByText('الرياض')).toBeInTheDocument() })
  it('renders deal count', () => { renderView(); expect(screen.getByText(/8 صفقات/)).toBeInTheDocument() })
  it('renders coverage gaps', () => { renderView(); expect(screen.getByText('القصيم')).toBeInTheDocument() })
  it('has role="region"', () => { renderView(); expect(screen.getByRole('region', { name: 'ذكاء المناطق' })).toBeInTheDocument() })
})
describe('TerritoryIntelligenceWidget', () => { it('is a valid widget', () => { expect(TerritoryIntelligenceWidget).toBeDefined() }) })
