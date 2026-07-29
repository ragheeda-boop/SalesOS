'use client'

import { setDashboardDependencies } from '@salesos/widget-sdk'
import { DashboardProvider, useDashboardContext } from '../_providers/dashboard-provider'
import { getWidgetConfig } from '../_registry/widget-config'
import { DashboardGrid } from './dashboard-grid'
import { DashboardLoading } from './dashboard-loading'
import { DashboardMetricsHeader } from './dashboard-metrics-header'
import { widgetRegistry } from '../widget-registry'
import { useTranslation } from '@/lib/i18n'

// Wire SDK to this app's dashboard context so widgets can read live data.
setDashboardDependencies(
  useDashboardContext,
  (id: string) => getWidgetConfig(id as Parameters<typeof getWidgetConfig>[0]),
)

function DashboardBody() {
 const { isLoading, isError, error, refetch } = useDashboardContext()
 const { t } = useTranslation()

 // Visible page-level h1 always present (loading / error / success) for a11y + smoke probes.
 return (
 <>
 <div className="mb-4">
 <h1 className="text-lg font-bold text-[var(--text-primary)]">{t("dashboard.title")}</h1>
 {!isLoading && !isError ? (
 <p className="text-xs text-[var(--text-muted)]">{t("dashboard.overview_subtitle")}</p>
 ) : null}
 </div>
 {isLoading ? (
 <DashboardLoading />
 ) : isError ? (
 <div
 role="alert"
 className="rounded-xl border border-danger-200 bg-danger-50 p-6 text-center dark:border-danger-800 dark:bg-danger-950/30"
 >
 <p className="text-sm font-semibold text-danger-800 dark:text-danger-200">{t("dashboard.load_error")}</p>
 <p className="mt-1 text-xs text-danger-600 dark:text-danger-400">{error?.message}</p>
 <button
 onClick={() => refetch()}
 className="mt-3 rounded-lg bg-[var(--muhide-orange)] px-4 py-2 text-xs font-semibold text-white transition-colors hover:opacity-90"
 >
 {t("common.retry")}
 </button>
 </div>
 ) : (
 <>
 <DashboardMetricsHeader />
 <DashboardGrid>
 {widgetRegistry.map((entry) => (
 <entry.Container key={entry.id} />
 ))}
 </DashboardGrid>
 </>
 )}
 </>
 )
}

export function DashboardPage() {
 return (
 <DashboardProvider>
 <DashboardBody />
 </DashboardProvider>
 )
}
