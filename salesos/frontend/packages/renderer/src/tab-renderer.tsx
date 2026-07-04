import { SectionRenderer } from './section-renderer'
import { WidgetRenderer } from './widget-renderer'
import type { UISchemaTab } from './types'

export interface TabRendererProps {
  tab: UISchemaTab
  entityType: string
  entityId: string
  context?: Record<string, unknown>
}

export function TabRenderer({ tab, entityType, entityId, context }: TabRendererProps) {
  return (
    <div className="space-y-6">
      {tab.sections?.map((section) => (
        <SectionRenderer
          key={section.id}
          section={section}
          entityType={entityType}
          entityId={entityId}
          context={context}
        />
      ))}
      {tab.widgetIds?.map((widgetId) => (
        <WidgetRenderer
          key={widgetId}
          widgetId={widgetId}
          entityType={entityType}
          entityId={entityId}
          context={context}
        />
      ))}
    </div>
  )
}
