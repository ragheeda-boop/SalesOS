'use client'

import { createDashboardWidget } from '@/features/dashboard/sdk'
import { YourWidgetView } from './YourWidgetView'
import type { YourWidgetData } from './types'

export const YourWidgetWidget = createDashboardWidget<YourWidgetData>('yourWidget', {
  metadata: {
    title: 'Your Widget',
    description: 'وصف الـ Widget',
  },
  render({ data }) {
    return (
      <YourWidgetView
        count={data.count}
        items={data.items}
        isLoading={false}
      />
    )
  },
})
