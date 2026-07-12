import { renderHook, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import type { ReactNode } from 'react'

jest.mock('@/lib/api')
jest.mock('@/lib/hooks/useTenant')

import api from '@/lib/api'
import { getTenantId } from '@/lib/hooks/useTenant'
import {
  useWorkflows, useWorkflow, useCreateWorkflow, useUpdateWorkflow,
  useDeleteWorkflow, useExecuteWorkflow, useWorkflowExecutions,
  workflowKeys,
} from '@/lib/workflowQueries'

const mockedApi = api as jest.Mocked<typeof api>
const mockedGetTenantId = getTenantId as jest.MockedFunction<typeof getTenantId>

beforeEach(() => {
  mockedGetTenantId.mockReturnValue('tenant-1')
})

function wrapper({ children }: { children: ReactNode }) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return <QueryClientProvider client={qc}>{children}</QueryClientProvider>
}

const sampleWorkflow = {
  id: 'wf-1',
  name: 'Test Workflow',
  description: 'A test workflow',
  trigger_type: 'manual' as const,
  trigger_config: {},
  steps: [],
  status: 'draft' as const,
  created_at: '2026-07-01T00:00:00Z',
  updated_at: '2026-07-10T00:00:00Z',
}

const sampleExecution = {
  id: 'exec-1',
  workflow_id: 'wf-1',
  status: 'success' as const,
  triggered_by: 'user-1',
  started_at: '2026-07-10T10:00:00Z',
  completed_at: '2026-07-10T10:01:00Z',
  error_message: null,
  step_results: [],
}

describe('workflowKeys', () => {
  it('generates consistent query keys', () => {
    expect(workflowKeys.all).toEqual(['workflows'])
    expect(workflowKeys.list({ status: 'active' })).toEqual(['workflows', 'list', { status: 'active' }])
    expect(workflowKeys.detail('wf-1')).toEqual(['workflows', 'detail', 'wf-1'])
    expect(workflowKeys.executions('wf-1')).toEqual(['workflows', 'executions', 'wf-1'])
  })
})

describe('useWorkflows', () => {
  it('fetches workflow list', async () => {
    mockedApi.get.mockResolvedValue({ data: [sampleWorkflow] })
    const { result } = renderHook(() => useWorkflows(), { wrapper })
    await waitFor(() => expect(result.current.isSuccess).toBe(true))
    expect(result.current.data).toEqual([sampleWorkflow])
  })
})

describe('useWorkflow', () => {
  it('fetches a single workflow', async () => {
    mockedApi.get.mockResolvedValue({ data: sampleWorkflow })
    const { result } = renderHook(() => useWorkflow('wf-1'), { wrapper })
    await waitFor(() => expect(result.current.isSuccess).toBe(true))
    expect(result.current.data).toEqual(sampleWorkflow)
  })
})

describe('useWorkflowExecutions', () => {
  it('fetches executions for a workflow', async () => {
    mockedApi.get.mockResolvedValue({ data: [sampleExecution] })
    const { result } = renderHook(() => useWorkflowExecutions('wf-1'), { wrapper })
    await waitFor(() => expect(result.current.isSuccess).toBe(true))
    expect(result.current.data).toEqual([sampleExecution])
  })
})

describe('useCreateWorkflow', () => {
  it('creates a workflow', async () => {
    mockedApi.post.mockResolvedValue({ data: sampleWorkflow })
    const { result } = renderHook(() => useCreateWorkflow(), { wrapper })
    result.current.mutate({ name: 'New Workflow' })
    await waitFor(() => expect(result.current.isSuccess).toBe(true))
    expect(result.current.data).toEqual(sampleWorkflow)
  })
})

describe('useUpdateWorkflow', () => {
  it('updates a workflow', async () => {
    mockedApi.put.mockResolvedValue({ data: sampleWorkflow })
    const { result } = renderHook(() => useUpdateWorkflow(), { wrapper })
    result.current.mutate({ id: 'wf-1', name: 'Updated' })
    await waitFor(() => expect(result.current.isSuccess).toBe(true))
    expect(result.current.data).toEqual(sampleWorkflow)
  })
})

describe('useDeleteWorkflow', () => {
  it('deletes a workflow', async () => {
    mockedApi.delete.mockResolvedValue({})
    const { result } = renderHook(() => useDeleteWorkflow(), { wrapper })
    result.current.mutate('wf-1')
    await waitFor(() => expect(result.current.isSuccess).toBe(true))
  })
})

describe('useExecuteWorkflow', () => {
  it('executes a workflow', async () => {
    mockedApi.post.mockResolvedValue({ data: sampleExecution })
    const { result } = renderHook(() => useExecuteWorkflow(), { wrapper })
    result.current.mutate('wf-1')
    await waitFor(() => expect(result.current.isSuccess).toBe(true))
    expect(result.current.data).toEqual(sampleExecution)
  })
})
