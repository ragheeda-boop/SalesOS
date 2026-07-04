import { WidgetRenderer } from './widget-renderer'
import { Badge } from '@salesos/ui'
import type { UISchemaSection } from './types'
import { cn } from '../../ui/src/utils'

export interface SectionRendererProps {
  section: UISchemaSection
  entityType: string
  entityId: string
  context?: Record<string, unknown>
}

function renderNode(node: any, index: number) {
  switch (node.type) {
    case 'text':
      return (
        <span key={index} className="text-sm text-gray-700 dark:text-gray-300">
          {node.value as string}
        </span>
      )
    case 'badge':
      return (
        <Badge key={index} variant={(node.props?.variant as any) || 'default'}>
          {node.value as string}
        </Badge>
      )
    case 'metric':
      return (
        <div key={index} className="rounded-lg border bg-white p-3 dark:border-gray-700 dark:bg-gray-900">
          {node.label && (
            <p className="text-xs text-gray-500 dark:text-gray-400">{node.label as string}</p>
          )}
          <p className="mt-1 text-xl font-semibold text-gray-900 dark:text-gray-100">
            {node.value as string}
          </p>
        </div>
      )
    case 'link':
      return (
        <a
          key={index}
          href={node.value as string}
          className="text-sm text-blue-600 hover:underline dark:text-blue-400"
        >
          {node.label as string}
        </a>
      )
    case 'list':
      return (
        <ul key={index} className="space-y-1">
          {(node.children as any[])?.map((child: any, ci: number) => (
            <li key={ci} className="text-sm text-gray-700 dark:text-gray-300">
              {child.value as string}
            </li>
          ))}
        </ul>
      )
    default:
      return null
  }
}

export function SectionRenderer({ section }: SectionRendererProps) {
  const columns = section.columns || 1
  const gridClass = columns === 1 ? '' : columns === 2 ? 'grid grid-cols-2 gap-4' : 'grid grid-cols-3 gap-4'

  return (
    <div>
      {section.title && (
        <h3 className="mb-3 text-sm font-semibold text-gray-900 dark:text-gray-100">{section.title}</h3>
      )}
      <div className={cn('space-y-4', gridClass)}>
        {section.nodes?.map((node, i) => renderNode(node, i))}
        {section.widgets?.map((widget) => (
          <WidgetRenderer key={widget.widgetId} widgetId={widget.widgetId} />
        ))}
      </div>
    </div>
  )
}
