'use client'

import { useDashboardContext } from '../../_providers/dashboard-provider'
import { WidgetCard } from '../widget-card'
import { CompanyHealthView } from './CompanyHealthView'
import { useCompanyDecision } from '../../../revenue-execution/_providers/DecisionProvider'
import { useNBAFeed } from '../../_hooks/useNBAFeed'
import type { CompanyHealthData } from './types'

export function CompanyHealthWidget() {
 const { widgets } = useDashboardContext()
 const widget = widgets.companyHealth
 const data = widget?.data as CompanyHealthData | null
 const tenantId = (data as { tenant_id?: string } | null)?.tenant_id ?? ''
 const decision = useCompanyDecision(tenantId)
 const nbaItems = useNBAFeed()
 return (
 <WidgetCard widget={widget} widgetId="companyHealth">
 {data ? (
 <CompanyHealthView
 overallScore={data.overallScore}
 metrics={data.metrics ?? []}
 alerts={data.alerts ?? []}
 companyName={data.companyName}
 decision={decision}
 nbaItems={nbaItems}
 isDecisionLoading={false}
 onAlertClick={(alertId) => {
 const alert = data.alerts?.find((a) => a.id === alertId)
 if (alert?.companyId) {
 window.location.href = `/companies/${alert.companyId}`
 }
 }}
 />
 ) : null}
 </WidgetCard>
 )
}
