'use client'

import Link from 'next/link'
import { useQuery } from '@tanstack/react-query'
import {
 ArrowUpRight,
 Activity,
 Building2,
 CheckSquare,
 ContactRound,
 Sparkles,
 Target,
 Users,
 BarChart3,
} from 'lucide-react'
import {
 getExecutiveDashboard,
 listOpportunities,
 searchCompanies,
 type Company,
 type Opportunity,
} from '@/lib/api'
import { companyKeys, dashboardKeys, opportunityKeys } from '@/lib/queryKeys'
import { getTenantId } from '@/lib/hooks/useTenant'
import { openV3AiPopup } from '@/components/v3/V3AiPopup'
import { PageHeader } from './_components/page-header'
import { MetricCards } from './_components/metric-cards'
import {
 EmptyState,
 ErrorState,
 GhostButtonLink,
 LoadingState,
 PermissionState,
} from './_components/states'
import { formatCount, formatCurrencySAR, formatPercent, stageLabel } from './_components/format'
import { useAccessToken } from './_hooks/useAccessToken'

const QUICK_ACTIONS = [
 {
 href: '/v3/companies',
 title: 'Companies',
 description: 'Browse accounts and open 360.',
 icon: Building2,
 },
 {
 href: '/v3/crm',
 title: 'Pipeline',
 description: 'Deals and opportunity stages.',
 icon: Target,
 },
 {
 href: '/v3/contacts',
 title: 'Contacts',
 description: 'Customer contacts and accounts.',
 icon: ContactRound,
 },
 {
 href: '/v3/people',
 title: 'People',
 description: 'Employees and owners.',
 icon: Users,
 },
 {
 href: '/v3/activities',
 title: 'Activities',
 description: 'Tenant activity feed.',
 icon: Activity,
 },
 {
 href: '/v3/tasks',
 title: 'Tasks',
 description: 'Open and completed follow-ups.',
 icon: CheckSquare,
 },
 {
 href: '/v3/analytics',
 title: 'Analytics',
 description: 'Live executive metrics + IA.',
 icon: BarChart3,
 },
] as const

function companyDisplayName(c: Company): string {
 return c.name_en?.trim() || c.name_ar || 'Untitled'
}

export default function V3HomePage() {
 const { ready, hasToken } = useAccessToken()
 const enabled = ready && hasToken

 const execQuery = useQuery({
 queryKey: dashboardKeys.exec(),
 queryFn: () => getExecutiveDashboard(getTenantId()),
 enabled,
 staleTime: 60_000,
 })

 const recentQuery = useQuery({
 queryKey: companyKeys.list({ page: 1, page_size: 5, sort_by: 'name_ar', sort_order: 'asc' }),
 queryFn: () =>
 searchCompanies(
 { page: 1, page_size: 5, sort_by: 'name_ar', sort_order: 'asc' },
 getTenantId(),
 ),
 enabled,
 staleTime: 15_000,
 })

 const dealsQuery = useQuery({
 queryKey: opportunityKeys.list(),
 queryFn: () => listOpportunities(getTenantId()),
 enabled,
 staleTime: 15_000,
 })

 const recent = recentQuery.data?.items ?? []
 const companyTotal = recentQuery.data?.total
 const topDeals: Opportunity[] = [...(dealsQuery.data?.items ?? [])]
 .sort((a, b) => (b.value || 0) - (a.value || 0))
 .slice(0, 5)

 const exec = execQuery.data

 return (
 <div className="mx-auto max-w-6xl space-y-8">
 <PageHeader
 title="Sales home"
 description="Workspace overview for SalesOS Design Program. AI opens only via Ask AI popup — never embedded in this page."
 actions={
 <button
 type="button"
 onClick={() => openV3AiPopup({ contextLabel: 'Sales home' })}
 className="inline-flex items-center gap-1.5 rounded-[var(--radius-md)] border border-[var(--border-default)] px-3 py-1.5 text-sm text-[var(--text-secondary)] hover:bg-[var(--bg-secondary)] hover:text-[var(--text-primary)] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--focus-ring)]"
 aria-haspopup="dialog"
 >
 <Sparkles className="h-3.5 w-3.5 text-[var(--muhide-orange)]" aria-hidden />
 Ask AI
 </button>
 }
 />

 <section aria-label="Key metrics">
 <div className="mb-3 flex items-baseline justify-between gap-2">
 <h2 className="text-sm font-medium text-[var(--text-primary)]">Key metrics</h2>
 <p className="text-[12px] text-[var(--text-muted)]">
 {execQuery.isFetching && !execQuery.isLoading
 ? 'Updating…'
 : 'From executive dashboard API'}
 </p>
 </div>

 {!ready ? (
 <LoadingState label="Checking session…" />
 ) : !hasToken ? (
 <PermissionState nextPath="/v3" />
 ) : execQuery.isLoading ? (
 <LoadingState label="Loading metrics…" />
 ) : execQuery.isError ? (
 <ErrorState
 title="Could not load metrics"
 description={
 execQuery.error instanceof Error
 ? execQuery.error.message
 : 'Executive dashboard unavailable'
 }
 onRetry={() => void execQuery.refetch()}
 />
 ) : !exec ? (
 <EmptyState
 title="No metrics yet"
 description="Executive dashboard returned empty for this tenant."
 action={<GhostButtonLink href="/v3/analytics">Open analytics</GhostButtonLink>}
 />
 ) : (
 <MetricCards
 items={[
 {
 label: 'Pipeline value',
 value: formatCurrencySAR(exec.pipeline.total_value),
 hint: `${formatCount(exec.pipeline.total_deals)} open deals`,
 },
 {
 label: 'Open deals',
 value: formatCount(exec.pipeline.total_deals),
 hint: `${formatCount(exec.risk.stalled_deals)} stalled`,
 },
 {
 label: 'Win rate',
 value: formatPercent(exec.pipeline.win_rate, { ratio: true }),
 hint: `${formatCount(exec.pipeline.won_deals)} won · ${formatCount(exec.pipeline.lost_deals)} lost`,
 },
 {
 label: 'Active team',
 value: formatCount(exec.team.active_employees),
 hint: `${formatCount(exec.team.total_employees)} total`,
 },
 ]}
 />
 )}
 </section>

 <section aria-label="Quick actions">
 <h2 className="mb-3 text-sm font-medium text-[var(--text-primary)]">Quick actions</h2>
 <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
 {QUICK_ACTIONS.map((action) => {
 const Icon = action.icon
 return (
 <Link
 key={action.href}
 href={action.href}
 className="group flex flex-col rounded-[var(--radius-lg)] border border-[var(--border-default)] bg-[var(--bg-primary)] p-4 transition-colors hover:border-[var(--border-hover)] hover:bg-[var(--bg-secondary)] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--focus-ring)]"
 >
 <div className="flex items-start justify-between gap-2">
 <span className="inline-flex h-8 w-8 items-center justify-center rounded-[var(--radius-md)] bg-[var(--bg-tertiary)] text-[var(--text-secondary)]">
 <Icon className="h-4 w-4" aria-hidden />
 </span>
 <ArrowUpRight
 className="h-3.5 w-3.5 text-[var(--text-muted)] opacity-0 transition-opacity group-hover:opacity-100"
 aria-hidden
 />
 </div>
 <h3 className="mt-3 text-sm font-medium text-[var(--text-primary)]">{action.title}</h3>
 <p className="mt-1 text-[12px] leading-relaxed text-[var(--text-muted)]">
 {action.description}
 </p>
 </Link>
 )
 })}
 </div>
 </section>

 <div className="grid gap-8 lg:grid-cols-2">
 <section aria-label="Recent companies" className="space-y-3">
 <div className="flex flex-wrap items-center justify-between gap-2">
 <h2 className="text-sm font-medium text-[var(--text-primary)]">Companies</h2>
 <GhostButtonLink href="/v3/companies">View all</GhostButtonLink>
 </div>

 {!ready ? (
 <LoadingState label="Checking session…" />
 ) : !hasToken ? (
 <PermissionState nextPath="/v3" />
 ) : recentQuery.isLoading ? (
 <LoadingState label="Loading companies…" />
 ) : recentQuery.isError ? (
 <EmptyState
 title="Could not load companies"
 description="Sign-in session may be expired, or the API is unavailable."
 action={<GhostButtonLink href="/v3/companies">Open Companies</GhostButtonLink>}
 />
 ) : recent.length === 0 ? (
 <EmptyState
 title="No companies yet"
 description="Import or create companies to populate this list."
 action={<GhostButtonLink href="/v3/companies">Go to Companies</GhostButtonLink>}
 />
 ) : (
 <ul className="overflow-hidden rounded-[var(--radius-lg)] border border-[var(--border-default)] bg-[var(--bg-primary)]">
 {recent.map((company) => (
 <li
 key={company.id}
 className="border-b border-[var(--border-default)] last:border-b-0"
 >
 <Link
 href={`/v3/companies/${company.id}`}
 className="flex items-center justify-between gap-3 px-4 py-3 text-sm hover:bg-[var(--bg-secondary)] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-[var(--focus-ring)]"
 >
 <span className="min-w-0">
 <span className="block truncate font-medium text-[var(--text-primary)]">
 {companyDisplayName(company)}
 </span>
 <span className="mt-0.5 block truncate text-[12px] text-[var(--text-muted)]">
 {[company.city, company.region].filter(Boolean).join(' · ') ||
 company.cr_number ||
 '—'}
 </span>
 </span>
 <ArrowUpRight
 className="h-3.5 w-3.5 shrink-0 text-[var(--text-muted)]"
 aria-hidden
 />
 </Link>
 </li>
 ))}
 {companyTotal != null ? (
 <li className="bg-[var(--bg-secondary)] px-4 py-2 text-[12px] text-[var(--text-muted)]">
 {companyTotal} compan{companyTotal === 1 ? 'y' : 'ies'} in tenant
 </li>
 ) : null}
 </ul>
 )}
 </section>

 <section aria-label="Top deals" className="space-y-3">
 <div className="flex flex-wrap items-center justify-between gap-2">
 <h2 className="text-sm font-medium text-[var(--text-primary)]">Top deals</h2>
 <GhostButtonLink href="/v3/crm">View pipeline</GhostButtonLink>
 </div>

 {!ready || !hasToken ? null : dealsQuery.isLoading ? (
 <LoadingState label="Loading deals…" />
 ) : dealsQuery.isError ? (
 <EmptyState
 title="Could not load deals"
 description="Opportunity list unavailable."
 action={<GhostButtonLink href="/v3/crm">Open CRM</GhostButtonLink>}
 />
 ) : topDeals.length === 0 ? (
 <EmptyState
 title="No deals yet"
 description="Create opportunities from a company record."
 action={<GhostButtonLink href="/v3/companies">Find a company</GhostButtonLink>}
 />
 ) : (
 <ul className="overflow-hidden rounded-[var(--radius-lg)] border border-[var(--border-default)] bg-[var(--bg-primary)]">
 {topDeals.map((opp) => (
 <li
 key={opp.id}
 className="border-b border-[var(--border-default)] last:border-b-0"
 >
 <Link
 href={`/v3/crm/${opp.id}`}
 className="flex items-center justify-between gap-3 px-4 py-3 text-sm hover:bg-[var(--bg-secondary)] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-[var(--focus-ring)]"
 >
 <span className="min-w-0">
 <span className="block truncate font-medium text-[var(--text-primary)]">
 {opp.name}
 </span>
 <span className="mt-0.5 block truncate text-[12px] capitalize text-[var(--text-muted)]">
 {stageLabel(opp.stage)}
 {opp.company_name ? ` · ${opp.company_name}` : ''}
 </span>
 </span>
 <span className="shrink-0 tabular-nums text-[var(--text-secondary)]">
 {formatCurrencySAR(opp.value)}
 </span>
 </Link>
 </li>
 ))}
 </ul>
 )}
 </section>
 </div>
 </div>
 )
}
