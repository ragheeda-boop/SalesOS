import { render, screen } from '@testing-library/react'
import { MultiWorkspaceView } from '../MultiWorkspaceView'
import { MultiWorkspaceWidget } from '../MultiWorkspaceContainer'
import { describeWidgetContract } from '@salesos/workspace/testing'
import type { WorkspaceData } from '../types'

const sample: WorkspaceData = { workspaces: [{ id: 'w1', name: 'لوحة القيادة', type: 'dashboard', active: true, lastAccessed: '2026-07-10' }], total: 1, active: 1 }
function renderView(d: WorkspaceData = sample) { return render(<MultiWorkspaceView data={d} />) }

describeWidgetContract({ name: 'MultiWorkspace', defaultData: sample, config: { metadata: { id: 'multiWorkspace', title: 'مساحات العمل', permissions: ['workspace:read'], featureFlag: { enabled: true } }, render: ({ data }) => <MultiWorkspaceView data={data} /> } })

describe('MultiWorkspaceView', () => {
  it('renders workspace name', () => { renderView(); expect(screen.getByText('لوحة القيادة')).toBeInTheDocument() })
  it('shows active badge', () => { renderView(); expect(screen.getByText('نشط')).toBeInTheDocument() })
  it('shows active count', () => { renderView(); expect(screen.getByText(/1 نشطة/)).toBeInTheDocument() })
  it('has role="region"', () => { renderView(); expect(screen.getByRole('region', { name: 'مساحات العمل' })).toBeInTheDocument() })
})
describe('MultiWorkspaceWidget', () => { it('is a valid widget', () => { expect(MultiWorkspaceWidget).toBeDefined() }) })
