import { Card, CardHeader, CardContent, Spinner } from '@salesos/ui'

export interface WidgetRendererProps {
  widgetId: string
  entityType?: string
  entityId?: string
  context?: Record<string, unknown>
  loading?: boolean
  error?: string
  children?: React.ReactNode
}

export function WidgetRenderer({ widgetId, loading, error, children }: WidgetRendererProps) {
  if (loading) {
    return (
      <Card>
        <CardHeader>
          <div className="h-4 w-32 animate-pulse rounded bg-gray-200 dark:bg-gray-700" />
        </CardHeader>
        <CardContent>
          <div className="flex h-32 items-center justify-center">
            <Spinner />
          </div>
        </CardContent>
      </Card>
    )
  }

  if (error) {
    return (
      <Card>
        <CardContent>
          <div className="rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700 dark:border-red-800 dark:bg-red-900/50 dark:text-red-400">
            {error}
          </div>
        </CardContent>
      </Card>
    )
  }

  return (
    <Card data-widget-id={widgetId}>
      {children}
    </Card>
  )
}
