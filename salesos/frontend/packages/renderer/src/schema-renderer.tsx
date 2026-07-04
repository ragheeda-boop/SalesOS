import { ViewerRenderer } from './viewer-renderer'
import type { UISchema } from './types'

export interface SchemaRendererProps {
  schema: UISchema
  loading?: boolean
  error?: string
  className?: string
}

export function SchemaRenderer({ schema, loading, error, className }: SchemaRendererProps) {
  if (loading) {
    return (
      <div className="flex h-64 items-center justify-center">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-blue-600 border-t-transparent" />
      </div>
    )
  }

  if (error) {
    return (
      <div className="flex h-64 items-center justify-center">
        <div className="rounded-lg border border-red-200 bg-red-50 p-4 text-red-700 dark:border-red-800 dark:bg-red-900/50 dark:text-red-400">
          {error}
        </div>
      </div>
    )
  }

  if (!schema) {
    return (
      <div className="flex h-64 items-center justify-center text-gray-500 dark:text-gray-400">
        No schema provided
      </div>
    )
  }

  return (
    <div className={className}>
      <ViewerRenderer
        entityType={schema.entityType}
        entityId={schema.entityId}
        tabs={schema.tabs}
        actions={schema.actions}
        context={schema.context}
      />
    </div>
  )
}
