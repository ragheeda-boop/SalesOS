'use client'

import { useMemo, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { getGlobalActivities } from '@/lib/api'
import { activityKeys } from '@/lib/queryKeys'
import { getTenantId } from '@/lib/hooks/useTenant'
import { openV3AiPopup } from '@/components/v3/V3AiPopup'
import { PageHeader } from '../_components/page-header'
import { ActivityFeed } from '../_components/activity-feed'
import {
 GhostButtonLink,
 LoadingState,
 PermissionState,
} from '../_components/states'
import { useAccessToken } from '../_hooks/useAccessToken'

const ACTION_FILTERS = [
 { label: 'All', value: '' },
 { label: 'Email', value: 'email' },
 { label: 'Meeting', value: 'meeting' },
 { label: 'Call', value: 'call' },
 { label: 'Task', value: 'task' },
 { label: 'Contract', value: 'contract' },
 { label: 'Note', value: 'note' },
 { label: 'Opportunity', value: 'opportunity' },
] as const

export default function V3ActivitiesPage() {
 const { ready, hasToken } = useAccessToken()
 const [actionFilter, setActionFilter] = useState('')
 const [q, setQ] = useState('')

 const filters = useMemo(() => {
 const f: { action?: string; limit: number } = { limit: 50 }
 if (actionFilter) f.action = actionFilter
 return f
 }, [actionFilter])

 const { data, isLoading, isError, error, refetch, isFetching } = useQuery({
 queryKey: activityKeys.global(filters),
 queryFn: () => getGlobalActivities(getTenantId(), filters),
 enabled: ready && hasToken,
 staleTime: 15_000,
 })

 const items = data?.items ?? []
 const total = data?.total ?? items.length

 const filtered = useMemo(() => {
 const needle = q.trim().toLowerCase()
 if (!needle) return items
 return items.filter((row) => {
 const hay = `${row.actor} ${row.action} ${row.entity_type} ${row.entity_id}`.toLowerCase()
 return hay.includes(needle)
 })
 }, [items, q])

 return (
 <div className="mx-auto max-w-6xl">
 <PageHeader
 title="Activities"
 description="Tenant activity feed — Design Program v3. Legacy /activities remains unchanged."
 actions={
 <div className="flex flex-wrap gap-2">
 <button
 type="button"
 onClick={() => openV3AiPopup({ contextLabel: 'Activities' })}
 className="rounded-[var(--radius-md)] border border-[var(--border-default)] px-3 py-1.5 text-[12px] font-medium text-[var(--text-secondary)] hover:bg-[var(--bg-secondary)]"
 >
 Ask AI
 </button>
 <GhostButtonLink href="/activities">Legacy activities</GhostButtonLink>
 </div>
 }
 />

 {!ready ? (
 <LoadingState label="Checking session…" />
 ) : !hasToken ? (
 <PermissionState nextPath="/v3/activities" />
 ) : (
 <div className="space-y-4">
 <div className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
 <div className="flex min-w-0 flex-1 flex-col gap-3 sm:flex-row sm:items-center">
 <label className="block min-w-0 flex-1">
 <span className="sr-only">Search activity</span>
 <input
 type="search"
 value={q}
 onChange={(e) => setQ(e.target.value)}
 placeholder="Search actor, action, entity…"
 className="w-full max-w-md rounded-[var(--radius-md)] border border-[var(--border-default)] bg-[var(--bg-primary)] px-3 py-2 text-sm outline-none focus:border-[var(--muhide-orange)] focus-visible:ring-2 focus-visible:ring-[var(--focus-ring)]"
 />
 </label>
 <div
 className="flex gap-1 overflow-x-auto rounded-[var(--radius-md)] border border-[var(--border-default)] px-1 py-0.5"
 role="group"
 aria-label="Filter by action"
 >
 {ACTION_FILTERS.map((f) => {
 const selected = actionFilter === f.value
 return (
 <button
 key={f.value || 'all'}
 type="button"
 onClick={() => setActionFilter(f.value)}
 className={
 selected
 ? 'whitespace-nowrap rounded-[var(--radius-sm)] bg-[var(--muhide-orange)] px-2.5 py-1 text-xs text-white'
 : 'whitespace-nowrap rounded-[var(--radius-sm)] px-2.5 py-1 text-xs text-[var(--text-secondary)] hover:text-[var(--text-primary)]'
 }
 >
 {f.label}
 </button>
 )
 })}
 </div>
 </div>
 <p className="text-[12px] text-[var(--text-muted)]" aria-live="polite">
 {isFetching && !isLoading ? 'Updating… · ' : null}
 {!isLoading && !isError
 ? `${filtered.length} shown${total ? ` · ${total} total` : ''}`
 : null}
 </p>
 </div>

 <ActivityFeed
 items={filtered}
 isLoading={isLoading}
 isError={isError}
 errorMessage={error instanceof Error ? error.message : undefined}
 onRetry={() => void refetch()}
 showEntity
 emptyTitle={items.length === 0 ? 'No activity yet' : 'No matching activity'}
 emptyDescription={
 items.length === 0
 ? 'The activities API returned no rows for this tenant. Nothing is invented here.'
 : 'Try a different filter or clear the search.'
 }
 emptyActionHref={q || actionFilter ? undefined : '/v3/crm'}
 emptyActionLabel={q || actionFilter ? undefined : 'Browse CRM'}
 />

 {(q || actionFilter) && items.length > 0 && filtered.length === 0 ? (
 <div className="flex justify-center">
 <button
 type="button"
 onClick={() => {
 setQ('')
 setActionFilter('')
 }}
 className="rounded-[var(--radius-md)] border border-[var(--border-default)] px-3 py-1.5 text-sm hover:bg-[var(--bg-secondary)]"
 >
 Clear filters
 </button>
 </div>
 ) : null}
 </div>
 )}
 </div>
 )
}
