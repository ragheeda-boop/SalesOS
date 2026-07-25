'use client'

import { ActivityTimeline } from './ActivityTimeline'
import { DecisionPlatformPanel } from './DecisionPlatformPanel'
import { KnowledgeGraphPanel } from './KnowledgeGraphPanel'
import type { Company360ViewProps } from './types'

export function Company360View({ companyId, company360 }: Company360ViewProps) {
 return (
 <div className="space-y-4" role="region" aria-label="نظرة شاملة للشركة">
 <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
 <DecisionPlatformPanel companyId={companyId} company360={company360 || undefined} />
 <KnowledgeGraphPanel companyId={companyId} company360={company360 || undefined} />
 </div>
 <ActivityTimeline companyId={companyId} />
 </div>
 )
}
