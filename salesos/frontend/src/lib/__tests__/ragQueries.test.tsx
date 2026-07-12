import { renderHook, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import type { ReactNode } from 'react'

jest.mock('@/lib/api')
jest.mock('@/lib/hooks/useTenant')

import api from '@/lib/api'
import { getTenantId } from '@/lib/hooks/useTenant'
import {
  useRagDocuments, useAskQuestion, useIngestDocument, useDeleteDocument,
  ragKeys,
} from '@/lib/ragQueries'

const mockedApi = api as jest.Mocked<typeof api>
const mockedGetTenantId = getTenantId as jest.MockedFunction<typeof getTenantId>

beforeEach(() => {
  mockedGetTenantId.mockReturnValue('tenant-1')
})

function wrapper({ children }: { children: ReactNode }) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return <QueryClientProvider client={qc}>{children}</QueryClientProvider>
}

const sampleDoc = { id: 'doc-1', title: 'Test Doc', content: 'Test content', source_type: 'note' as const, created_at: '2026-07-01T00:00:00Z' }

describe('ragKeys', () => {
  it('generates consistent query keys', () => {
    expect(ragKeys.all).toEqual(['rag'])
    expect(ragKeys.documents()).toEqual(['rag', 'documents'])
    expect(ragKeys.document('doc-1')).toEqual(['rag', 'documents', 'doc-1'])
  })
})

describe('useRagDocuments', () => {
  it('fetches RAG documents', async () => {
    mockedApi.get.mockResolvedValue({ data: [sampleDoc] })
    const { result } = renderHook(() => useRagDocuments(), { wrapper })
    await waitFor(() => expect(result.current.isSuccess).toBe(true))
    expect(result.current.data).toEqual([sampleDoc])
  })
})

describe('useAskQuestion', () => {
  it('posts a question and returns answer', async () => {
    mockedApi.post.mockResolvedValue({ data: { answer: 'Test answer', citations: [] } })
    const { result } = renderHook(() => useAskQuestion(), { wrapper })
    result.current.mutate('What is this?')
    await waitFor(() => expect(result.current.isSuccess).toBe(true))
    expect(result.current.data?.answer).toBe('Test answer')
  })
})

describe('useIngestDocument', () => {
  it('ingests a document', async () => {
    mockedApi.post.mockResolvedValue({ data: sampleDoc })
    const { result } = renderHook(() => useIngestDocument(), { wrapper })
    result.current.mutate({ title: 'New Doc', content: 'Content', source_type: 'note' })
    await waitFor(() => expect(result.current.isSuccess).toBe(true))
    expect(result.current.data).toEqual(sampleDoc)
  })
})

describe('useDeleteDocument', () => {
  it('deletes a document', async () => {
    mockedApi.delete.mockResolvedValue({})
    const { result } = renderHook(() => useDeleteDocument(), { wrapper })
    result.current.mutate('doc-1')
    await waitFor(() => expect(result.current.isSuccess).toBe(true))
  })
})
