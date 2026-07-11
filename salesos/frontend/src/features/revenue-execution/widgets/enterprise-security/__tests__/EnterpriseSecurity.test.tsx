import { render, screen } from '@testing-library/react'
import { SecurityView } from '../SecurityView'
import { EnterpriseSecurityWidget } from '../SecurityContainer'
import { describeWidgetContract } from '@salesos/workspace/testing'
import type { SecurityData } from '../types'

const sample: SecurityData = { ssoEnabled: true, rbacEnabled: true, auditEnabled: true, mfaEnabled: false, activeUsers: 24, roles: 6, auditEvents: 15000, pendingActions: 2, recentAudit: [] }
function renderView(d: SecurityData = sample) { return render(<SecurityView data={d} />) }

describeWidgetContract({ name: 'EnterpriseSecurity', defaultData: sample, config: { metadata: { id: 'enterpriseSecurity', title: 'الأمان', permissions: ['enterprise:security:read'], featureFlag: { enabled: true } }, render: ({ data }) => <SecurityView data={data} /> } })

describe('SecurityView', () => {
  it('renders SSO badge', () => { renderView(); expect(screen.getByText('SSO')).toBeInTheDocument() })
  it('renders active users', () => { renderView(); expect(screen.getByText('24')).toBeInTheDocument() })
  it('renders roles', () => { renderView(); expect(screen.getByText('6')).toBeInTheDocument() })
  it('renders pending actions', () => { renderView(); expect(screen.getByText('2')).toBeInTheDocument() })
  it('has role="region"', () => { renderView(); expect(screen.getByRole('region', { name: 'الأمان' })).toBeInTheDocument() })
})
describe('EnterpriseSecurityWidget', () => { it('is a valid widget', () => { expect(EnterpriseSecurityWidget).toBeDefined() }) })
