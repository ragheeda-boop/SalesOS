import { useState } from 'react'
import { Tabs, TabsList, Tab, TabsPanel, Button } from '@salesos/ui'
import { TabRenderer } from './tab-renderer'
import type { UISchemaTab, UIAction } from './types'
import { cn } from '../../ui/src/utils'

export interface ViewerRendererProps {
  entityType: string
  entityId: string
  tabs: UISchemaTab[]
  actions?: UIAction[]
  context?: Record<string, unknown>
  className?: string
}

export function ViewerRenderer({ entityType, entityId, tabs, actions, context, className }: ViewerRendererProps) {
  const [activeTab, setActiveTab] = useState(tabs[0]?.id)

  const actionIcons: Record<string, React.ReactNode> = {}

  return (
    <div className={cn('space-y-6', className)}>
      {actions && actions.length > 0 && (
        <div className="flex items-center justify-end gap-2">
          {actions.map((action) => (
            <Button key={action.id} variant={action.variant || 'secondary'} size="sm">
              {actionIcons[action.icon || '']}
              {action.label}
            </Button>
          ))}
        </div>
      )}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList>
          {tabs.map((tab) => (
            <Tab key={tab.id} value={tab.id}>
              {tab.title}
            </Tab>
          ))}
        </TabsList>
        {tabs.map((tab) => (
          <TabsPanel key={tab.id} value={tab.id}>
            <TabRenderer tab={tab} entityType={entityType} entityId={entityId} context={context} />
          </TabsPanel>
        ))}
      </Tabs>
    </div>
  )
}
