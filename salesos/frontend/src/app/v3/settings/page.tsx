'use client'

import { useMemo, type ReactNode } from 'react'
import { useQuery } from '@tanstack/react-query'
import { getApiKeys, getNotificationPreferences, type ApiKeyRecord } from '@/lib/api'
import { settingsKeys } from '@/lib/queryKeys'
import { getTenantId } from '@/lib/hooks/useTenant'
import { openV3AiPopup } from '@/components/v3/V3AiPopup'
import { PageHeader } from '../_components/page-header'
import { DomainWorkbench, type DomainSection } from '../_components/domain-workbench'
import {
 EmptyState,
 ErrorState,
 GhostButtonLink,
 LoadingState,
 PermissionState,
 PreviewBadge,
} from '../_components/states'
import { formatWhen } from '../_components/format'
import { useAccessToken } from '../_hooks/useAccessToken'

function PreviewPanel({
 children,
 legacyHref,
 legacyLabel = 'Legacy settings',
}: {
 children: ReactNode
 legacyHref?: string
 legacyLabel?: string
}) {
 return (
 <div className="space-y-3 text-sm text-[var(--text-secondary)]">
 <div className="flex items-center gap-2">
 <PreviewBadge />
 <span className="text-[12px] text-[var(--text-muted)]">Not wired</span>
 </div>
 <p>{children}</p>
 {legacyHref ? <GhostButtonLink href={legacyHref}>{legacyLabel}</GhostButtonLink> : null}
 </div>
 )
}

function NotificationsPanel({ ready, hasToken }: { ready: boolean; hasToken: boolean }) {
 const query = useQuery({
 queryKey: settingsKeys.notifications(),
 queryFn: () => getNotificationPreferences(getTenantId()),
 enabled: ready && hasToken,
 staleTime: 30_000,
 })

 if (query.isLoading) return <LoadingState label="Loading notification preferences…" />
 if (query.isError) {
 return (
 <ErrorState
 title="Could not load notifications"
 description={query.error instanceof Error ? query.error.message : 'Request failed'}
 onRetry={() => void query.refetch()}
 />
 )
 }

 const prefs = query.data
 if (!prefs) {
 return (
 <EmptyState
 title="No preferences"
 description="Settings API returned empty notification preferences."
 action={<GhostButtonLink href="/settings">Open legacy settings</GhostButtonLink>}
 />
 )
 }

 const rows: { label: string; on: boolean }[] = [
 { label: 'Email notifications', on: prefs.email_notifications },
 { label: 'In-app notifications', on: prefs.app_notifications },
 { label: 'Opportunity alerts', on: prefs.opportunity_alerts },
 { label: 'Company updates', on: prefs.company_updates },
 { label: 'Weekly summary', on: prefs.weekly_summary },
 ]

 return (
 <div className="space-y-3">
 <p className="text-sm text-[var(--text-secondary)]">
 Read-only dual-run view of{' '}
 <code className="font-mono text-[12px]">GET /api/v1/settings/notifications</code>. Edit in
 legacy settings to avoid accidental preference writes from the spike shell.
 </p>
 <ul className="overflow-hidden rounded-[var(--radius-md)] border border-[var(--border-default)]">
 {rows.map((row) => (
 <li
 key={row.label}
 className="flex items-center justify-between gap-3 border-b border-[var(--border-default)] px-3 py-2.5 text-sm last:border-b-0"
 >
 <span className="text-[var(--text-primary)]">{row.label}</span>
 <span className={row.on ? 'text-[var(--text-secondary)]' : 'text-[var(--text-muted)]'}>
 {row.on ? 'On' : 'Off'}
 </span>
 </li>
 ))}
 </ul>
 <GhostButtonLink href="/settings">Edit in legacy settings</GhostButtonLink>
 </div>
 )
}

function ApiKeysPanel({ ready, hasToken }: { ready: boolean; hasToken: boolean }) {
 const query = useQuery({
 queryKey: settingsKeys.apiKeys(),
 queryFn: () => getApiKeys(getTenantId()),
 enabled: ready && hasToken,
 staleTime: 30_000,
 })

 if (query.isLoading) return <LoadingState label="Loading API keys…" />
 if (query.isError) {
 return (
 <ErrorState
 title="Could not load API keys"
 description={query.error instanceof Error ? query.error.message : 'Request failed'}
 onRetry={() => void query.refetch()}
 />
 )
 }

 const keys: ApiKeyRecord[] = query.data ?? []
 if (keys.length === 0) {
 return (
 <EmptyState
 title="No API keys"
 description="Create and rotate keys in legacy settings — dual-run is list-only."
 action={<GhostButtonLink href="/settings">Open legacy settings</GhostButtonLink>}
 />
 )
 }

 return (
 <div className="space-y-3">
 <p className="text-sm text-[var(--text-secondary)]">
 Previews only — full secrets are never shown. Create/delete stays in legacy.
 </p>
 <ul className="overflow-hidden rounded-[var(--radius-md)] border border-[var(--border-default)]">
 {keys.map((key) => (
 <li
 key={key.id}
 className="flex flex-wrap items-baseline justify-between gap-2 border-b border-[var(--border-default)] px-3 py-2.5 text-sm last:border-b-0"
 >
 <span>
 <span className="font-medium text-[var(--text-primary)]">{key.name}</span>
 <span className="mt-0.5 block font-mono text-[12px] text-[var(--text-muted)]">
 {key.key_preview}
 </span>
 </span>
 <span className="text-[12px] text-[var(--text-muted)]">{formatWhen(key.created_at)}</span>
 </li>
 ))}
 </ul>
 <GhostButtonLink href="/settings">Manage keys in legacy</GhostButtonLink>
 </div>
 )
}

export default function V3SettingsPage() {
 const { ready, hasToken } = useAccessToken()

 const sections: DomainSection[] = useMemo(
 () => [
 {
 id: 'workspace',
 label: 'Workspace',
 audience: 'Admins',
 description: 'Name, branding, defaults, and enabled modules.',
 body: (
 <PreviewPanel legacyHref="/settings">
 Workspace branding/module toggles are not dual-run yet. Prefer legacy settings for
 tenant-wide changes.
 </PreviewPanel>
 ),
 },
 {
 id: 'personal',
 label: 'Personal',
 audience: 'All',
 description: 'Profile, signature, and personal preferences.',
 body: (
 <PreviewPanel legacyHref="/settings">
 Personal profile editing remains on legacy settings for this spike.
 </PreviewPanel>
 ),
 },
 {
 id: 'security',
 label: 'Security',
 audience: 'Admins + self',
 description: 'MFA, active sessions, and SSO enrollment.',
 body: (
 <PreviewPanel legacyHref="/settings">
 MFA / session policy is not dual-run. Do not weaken auth from this shell.
 </PreviewPanel>
 ),
 },
 {
 id: 'billing',
 label: 'Billing',
 audience: 'Billing admins',
 description: 'Plan, invoices, and payment methods.',
 body: (
 <PreviewPanel legacyHref="/settings">
 Billing actions stay out of dual-run to avoid accidental commercial changes.
 </PreviewPanel>
 ),
 },
 {
 id: 'notifications',
 label: 'Notifications',
 audience: 'All',
 description: 'Channels, digests, and quiet hours — preferences from settings API.',
 body:
 ready && hasToken ? (
 <NotificationsPanel ready={ready} hasToken={hasToken} />
 ) : !ready ? (
 <LoadingState />
 ) : (
 <PermissionState nextPath="/v3/settings" />
 ),
 },
 {
 id: 'api',
 label: 'API',
 audience: 'Admins',
 description: 'API keys and outbound webhooks — list/preview only.',
 body:
 ready && hasToken ? (
 <ApiKeysPanel ready={ready} hasToken={hasToken} />
 ) : !ready ? (
 <LoadingState />
 ) : (
 <PermissionState nextPath="/v3/settings" />
 ),
 },
 {
 id: 'integrations',
 label: 'Integrations',
 audience: 'Admins',
 description: 'Connected apps for mail, calendar, and CRM sync.',
 body: (
 <PreviewPanel legacyHref="/settings">
 Integration connectors are not dual-run on this page.
 </PreviewPanel>
 ),
 },
 {
 id: 'ai',
 label: 'AI',
 audience: 'Admins + users',
 description: 'Model prefs, Preview flags, retention. AI opens via popup only.',
 body: (
 <div className="space-y-3 text-sm text-[var(--text-secondary)]">
 <p>
 Copilot is Preview-gated. There is no settings page AI rail — use Ask AI from the
 topbar or the button below. Humans decide; evidence governs.
 </p>
 <div className="flex flex-wrap gap-2">
 <button
 type="button"
 onClick={() => openV3AiPopup({ contextLabel: 'Settings · AI' })}
 className="rounded-[var(--radius-md)] border border-[var(--border-default)] px-3 py-1.5 text-sm hover:bg-[var(--bg-secondary)] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--focus-ring)]"
 >
 Open Ask AI popup
 </button>
 <GhostButtonLink href="/settings">Legacy settings</GhostButtonLink>
 </div>
 </div>
 ),
 },
 {
 id: 'appearance',
 label: 'Appearance',
 audience: 'All',
 description: 'Theme and density. Theme toggle also lives in the topbar.',
 body: (
 <PreviewPanel>
 Theme toggle lives in the v3 topbar. Density preferences are not dual-run yet.
 </PreviewPanel>
 ),
 },
 {
 id: 'language',
 label: 'Language',
 audience: 'All',
 description: 'Locale and RTL preferences.',
 body: (
 <PreviewPanel legacyHref="/settings">
 Locale / RTL preferences remain on legacy settings.
 </PreviewPanel>
 ),
 },
 {
 id: 'accessibility',
 label: 'Accessibility',
 audience: 'All',
 description: 'Reduced motion, contrast, and focus preferences.',
 body: (
 <PreviewPanel legacyHref="/settings">
 Accessibility preference store is not dual-run yet. Focus rings and skip link already
 ship in the v3 shell chrome.
 </PreviewPanel>
 ),
 },
 ],
 [ready, hasToken],
 )

 return (
 <div className="mx-auto max-w-6xl space-y-4">
 <PageHeader
 title="Settings"
 description="Settings domain with left subnav — notifications and API keys list from real settings APIs."
 actions={<GhostButtonLink href="/settings">Legacy settings</GhostButtonLink>}
 />
 {!ready ? (
 <LoadingState label="Checking session…" />
 ) : !hasToken ? (
 <PermissionState nextPath="/v3/settings" />
 ) : (
 <DomainWorkbench sections={sections} defaultId="notifications" />
 )}
 </div>
 )
}
