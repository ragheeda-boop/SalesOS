import { render, screen } from '@testing-library/react'
import { APIView } from '../APIView'
import { APIPlatformWidget } from '../APIContainer'
import { describeWidgetContract } from '@salesos/workspace/testing'
import type { APIData } from '../types'

const sample: APIData = { endpoints: [{ method: 'GET', path: '/api/v1/test', description: 'اختبار', calls: 100, avgLatency: 45 }], totalEndpoints: 1, totalCalls: 100, avgLatency: 45, errorRate: 0 }
function renderView(d: APIData = sample) { return render(<APIView data={d} />) }

describeWidgetContract({ name: 'APIPlatform', defaultData: sample, config: { metadata: { id: 'apiPlatform', title: 'منصة API', permissions: ['enterprise:api:read'], featureFlag: { enabled: true } }, render: ({ data }) => <APIView data={data} /> } })

describe('APIView', () => {
  it('renders endpoint path', () => { renderView(); expect(screen.getByText('/api/v1/test')).toBeInTheDocument() })
  it('renders endpoint count', () => { renderView(); expect(screen.getByText('1')).toBeInTheDocument() })
  it('renders total calls', () => { renderView(); const c = screen.getAllByText('100'); expect(c.length).toBeGreaterThanOrEqual(1) })
  it('renders latency', () => { renderView(); const l = screen.getAllByText('45ms'); expect(l.length).toBeGreaterThanOrEqual(1) })
  it('has role="region"', () => { renderView(); expect(screen.getByRole('region', { name: 'منصة API' })).toBeInTheDocument() })
})
describe('APIPlatformWidget', () => { it('is a valid widget', () => { expect(APIPlatformWidget).toBeDefined() }) })

