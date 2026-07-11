'use client'

import { createDashboardWidget } from '../../sdk/create-dashboard-widget'
import { MissionCenterView } from './MissionCenterView'
import type { MissionCenterData } from '@/application/dashboard/dashboard.dto'

export const MissionCenterWidget = createDashboardWidget<MissionCenterData>('missionCenter', {
  metadata: {
    title: 'Mission Center',
    description: 'نظرة سريعة على مؤشرات المهمة الرئيسية',
    priority: 'high',
    category: 'metrics',
    icon: '🎯',
  },
  render({ data }) {
    return (
      <MissionCenterView
        companiesTracked={data.companiesTracked}
        activeDeals={data.activeDeals}
        pipelineValue={data.pipelineValue}
        signalsToday={data.signalsToday}
        decisionsPending={data.decisionsPending}
      />
    )
  },
})
