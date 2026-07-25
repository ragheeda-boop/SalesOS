'use client'

import { useMemo, useState } from 'react'
import Link from 'next/link'
import { useQuery } from '@tanstack/react-query'
import { useDebounce } from '@salesos/hooks'
import { searchCompanies, type Company } from '@/lib/api'
import { companyKeys } from '@/lib/queryKeys'
import { getTenantId } from '@/lib/hooks/useTenant'
import { PageHeader } from '../_components/page-header'
import {
 EmptyState,
 ErrorState,
 GhostButtonLink,
 LoadingState,
 PermissionState,
} from '../_components/states'
import { useAccessToken } from '../_hooks/useAccessToken'

type SortOrder = 'asc' | 'desc'

function companyDisplayName(c: Company): string {
 return c.name_en?.trim() || c.name_ar || 'Untitled'
}

function statusLabel(status: string | null | undefined): string {
 if (!status) return '—'
 return status.replace(/_/g, ' ')
}

export default function V3CompaniesPage() {
 const { ready, hasToken } = useAccessToken()
 const [q, setQ] = useState('')
 const [sortOrder, setSortOrder] = useState<SortOrder>('asc')
 const debouncedQ = useDebounce(q, 400)

 const params = useMemo(
 () => ({
 q: debouncedQ || undefined,
 page: 1,
 page_size: 50,
 sort_by: 'name_ar',
 sort_order: sortOrder,
 }),
 [debouncedQ, sortOrder],
 )

 const { data, isLoading, isError, error, refetch, isFetching } = useQuery({
 queryKey: companyKeys.list(params as Record<string, unknown>),
 queryFn: () => searchCompanies(params, getTenantId()),
 enabled: ready && hasToken,
 staleTime: 10_000,
 })

 const items = data?.items ?? []
 const total = data?.total ?? 0

 return (
 <div className="mx-auto max-w-6xl">
 <PageHeader
 title="Companies"
 description="Enterprise Data Grid lite — Design Program v3. Legacy /companies is unchanged."
 />

 {!ready ? (
 <LoadingState label="Checking session…" />
 ) : !hasToken ? (
 <PermissionState nextPath="/v3/companies" />
 ) : (
 <div className="space-y-4">
 <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
 <label className="block min-w-0 flex-1">
 <span className="sr-only">Search companies</span>
 <input
 type="search"
 value={q}
 onChange={(e) => setQ(e.target.value)}
 placeholder="Search by name or CR…"
 className="w-full max-w-md rounded-[var(--radius-md)] border border-[var(--border-default)] bg-[var(--bg-primary)] px-3 py-2 text-sm outline-none focus:border-[var(--muhide-orange)] focus-visible:ring-2 focus-visible:ring-[var(--focus-ring)]"
 />
 </label>
 <p className="text-[12px] text-[var(--text-muted)]" aria-live="polite">
 {isFetching && !isLoading ? 'Updating… · ' : null}
 {!isLoading && !isError ? `${total} result${total === 1 ? '' : 's'}` : null}
 </p>
 </div>

 {isLoading ? (
 <LoadingState label="Loading companies…" />
 ) : isError ? (
 <ErrorState
 title="Could not load companies"
 description={error instanceof Error ? error.message : 'Request failed'}
 onRetry={() => void refetch()}
 />
 ) : items.length === 0 ? (
 <EmptyState
 title="No companies found"
 description={
 debouncedQ
 ? 'Try a different search, or clear the filter.'
 : 'No companies in this tenant yet.'
 }
 action={
 debouncedQ ? (
 <button
 type="button"
 onClick={() => setQ('')}
 className="rounded-[var(--radius-md)] border border-[var(--border-default)] px-3 py-1.5 text-sm hover:bg-[var(--bg-secondary)]"
 >
 Clear search
 </button>
 ) : (
 <GhostButtonLink href="/companies">Open legacy companies</GhostButtonLink>
 )
 }
 />
 ) : (
 <div className="overflow-hidden rounded-[var(--radius-lg)] border border-[var(--border-default)] bg-[var(--bg-primary)]">
 <div className="overflow-x-auto">
 <table className="w-full min-w-[640px] border-collapse text-left text-sm">
 <thead className="border-b border-[var(--border-default)] bg-[var(--bg-secondary)] text-[11px] uppercase tracking-[0.06em] text-[var(--text-muted)]">
 <tr>
 <th scope="col" className="px-3 py-2.5 font-medium">
 <button
 type="button"
 onClick={() => setSortOrder((prev) => (prev === 'asc' ? 'desc' : 'asc'))}
 className="inline-flex items-center gap-1 hover:text-[var(--text-primary)] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--focus-ring)]"
 aria-label={`Sort by name, currently ${sortOrder === 'asc' ? 'ascending' : 'descending'}`}
 >
 Name
 <span aria-hidden="true">{sortOrder === 'asc' ? '↑' : '↓'}</span>
 </button>
 </th>
 <th scope="col" className="px-3 py-2.5 font-medium">
 CR
 </th>
 <th scope="col" className="px-3 py-2.5 font-medium">
 Status
 </th>
 <th scope="col" className="px-3 py-2.5 font-medium">
 City
 </th>
 <th scope="col" className="px-3 py-2.5 font-medium">
 Region
 </th>
 </tr>
 </thead>
 <tbody>
 {items.map((company) => (
 <tr
 key={company.id}
 className="border-b border-[var(--border-default)] last:border-b-0 hover:bg-[var(--bg-secondary)]"
 >
 <td className="px-3 py-2.5">
 <Link
 href={`/v3/companies/${company.id}`}
 className="font-medium text-[var(--text-primary)] hover:underline focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--focus-ring)]"
 >
 {companyDisplayName(company)}
 </Link>
 {company.name_en && company.name_ar ? (
 <p className="mt-0.5 text-[12px] text-[var(--text-muted)]" dir="auto">
 {company.name_ar}
 </p>
 ) : null}
 </td>
 <td className="px-3 py-2.5 font-mono text-[12px] text-[var(--text-secondary)]">
 {company.cr_number || '—'}
 </td>
 <td className="px-3 py-2.5 capitalize text-[var(--text-secondary)]">
 {statusLabel(company.status)}
 </td>
 <td className="px-3 py-2.5 text-[var(--text-secondary)]">
 {company.city || '—'}
 </td>
 <td className="px-3 py-2.5 text-[var(--text-secondary)]">
 {company.region || '—'}
 </td>
 </tr>
 ))}
 </tbody>
 </table>
 </div>
 </div>
 )}
 </div>
 )}
 </div>
 )
}
