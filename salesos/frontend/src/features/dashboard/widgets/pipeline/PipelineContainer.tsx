'use client'

import { useDashboardContext } from '../../_providers/dashboard-provider'
import { WidgetCard } from '../widget-card'
import { PipelineView } from './PipelineView'
import { useCompanyDecision } from '../../../revenue-execution/_providers/DecisionProvider'
import { useNBAFeed } from '../../_hooks/useNBAFeed'
import type { PipelineData } from './types'

export function PipelineWidget() {
 const { widgets } = useDashboardContext()
 const widget = widgets.pipeline
 const data = widget?.data as PipelineData | null
 const tenantId = (data as { tenant_id?: string } | null)?.tenant_id ?? ''
 const decision = useCompanyDecision(tenantId)
 const nbaItems = useNBAFeed()
 return (
 <WidgetCard widget={widget} widgetId="pipeline">
 {data ? (
 <PipelineView
 stages={(data as PipelineData).stages ?? []}
 deals={(data as PipelineData).deals ?? []}
 totalValue={(data as PipelineData).totalValue ?? 0}
 dealCount={(data as PipelineData).dealCount ?? 0}
 decision={decision}
 nbaItems={nbaItems}
 isDecisionLoading={false}
 onDealClick={(dealId) => {
 window.location.href = `/companies/${data.deals?.find((d) => d.id === dealId)?.companyId ?? dealId}`
 }}
 />
 ) : null}
 </WidgetCard>
 )
}
