'use client'

import { useDashboardContext } from '../../_providers/dashboard-provider'
import { WidgetCard } from '../widget-card'
import { DecisionQueueView } from './DecisionQueueView'
import { useCompanyDecision } from '../../../revenue-execution/_providers/DecisionProvider'
import { useNBAFeed } from '../../_hooks/useNBAFeed'

export function DecisionQueueWidget() {
 const { widgets } = useDashboardContext()
 const widget = widgets.decisionQueue
 const data = widget?.data
 const tenantId = (data as { tenant_id?: string } | null)?.tenant_id ?? ''
 const decision = useCompanyDecision(tenantId)
 const nbaItems = useNBAFeed()
 return (
 <WidgetCard widget={widget} widgetId="decisionQueue">
 {data ? (
 <DecisionQueueView
 items={data.items ?? []}
 total={data.total ?? 0}
 decision={decision}
 nbaItems={nbaItems}
 isDecisionLoading={false}
 onItemClick={(id) => {
 window.location.href = `/companies/${data.items?.find((i) => i.id === id)?.companyId ?? id}`
 }}
 />
 ) : null}
 </WidgetCard>
 )
}
