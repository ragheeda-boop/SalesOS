import { useState } from 'react'
import { SchemaRenderer, type UISchema } from '@salesos/renderer'
import { cn } from '@salesos/ui'
import { AI_ACTIONS, type AIAction } from '@salesos/design-language'
import { useSchema, useLocalization, useRuntime } from '@salesos/hooks'
import {
  Clock, Sparkles, Zap, Share2, Activity, Maximize2, Minimize2, Bot, Loader2,
} from 'lucide-react'

export interface WorkspaceRendererProps {
  schema: UISchema
  loading?: boolean
  error?: string
  entityType?: string
  entityId?: string
  className?: string
}

export function WorkspaceRenderer({
  schema,
  loading,
  error,
  entityType,
  entityId,
  className,
}: WorkspaceRendererProps) {
  const { t } = useLocalization()
  const [activeView, setActiveView] = useState('overview' as string)
  const [copilotOpen, setCopilotOpen] = useState(false)
  const [fullscreen, setFullscreen] = useState(false)

  const secondaryViews = [
    { id: 'overview', label: 'نظرة عامة', icon: Activity },
    { id: 'timeline', label: 'النشاطات', icon: Clock },
    { id: 'ai', label: 'AI', icon: Sparkles },
    { id: 'signals', label: 'الإشارات', icon: Zap },
    { id: 'graph', label: 'العلاقات', icon: Share2 },
  ]

  const activeTab = schema.tabs.find((t) => t.id === activeView) || schema.tabs[0]
  const filteredTabs = activeView === 'overview'
    ? schema.tabs.filter((t) => !['timeline', 'ai', 'signals', 'graph'].includes(t.id))
    : [activeTab]

  const renderableSchema: UISchema = {
    ...schema,
    tabs: filteredTabs,
  }

  return (
    <div className={cn('flex flex-col', fullscreen && 'fixed inset-0 z-40 bg-white dark:bg-gray-950', className)}>
      <div className="flex items-center justify-between border-b border-gray-200 bg-white px-6 py-3 dark:border-gray-700 dark:bg-gray-900">
        <div className="flex items-center gap-2">
          {secondaryViews.map((view) => {
            const Icon = view.icon
            const isActive = activeView === view.id
            return (
              <button
                key={view.id}
                onClick={() => setActiveView(view.id)}
                className={cn(
                  'flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-sm transition',
                  isActive
                    ? 'bg-blue-50 text-blue-700 dark:bg-blue-900/50 dark:text-blue-300'
                    : 'text-gray-500 hover:bg-gray-100 dark:text-gray-400 dark:hover:bg-gray-800'
                )}
              >
                <Icon className="h-4 w-4" />
                <span className="hidden sm:inline">{view.label}</span>
              </button>
            )
          })}
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => setCopilotOpen(!copilotOpen)}
            className="flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-sm text-purple-600 hover:bg-purple-50 dark:text-purple-400 dark:hover:bg-purple-900/50"
          >
            <Bot className="h-4 w-4" />
            <span className="hidden sm:inline">AI</span>
          </button>
          <button
            onClick={() => setFullscreen(!fullscreen)}
            className="rounded-lg p-1.5 text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800"
          >
            {fullscreen ? <Minimize2 className="h-4 w-4" /> : <Maximize2 className="h-4 w-4" />}
          </button>
        </div>
      </div>
      <div className="flex flex-1 overflow-hidden">
        <div className={cn('flex-1 overflow-auto p-6', copilotOpen && 'ml-0')}>
          <div className="mx-auto" style={{ maxWidth: 1200 }}>
            <SchemaRenderer schema={renderableSchema} loading={loading} error={error} />
          </div>
        </div>
        {copilotOpen && (
          <aside className="w-80 border-r bg-gray-50 p-4 dark:border-gray-700 dark:bg-gray-900/50">
            <div className="flex items-center gap-2 border-b border-gray-200 pb-3 dark:border-gray-700">
              <Sparkles className="h-4 w-4 text-purple-600" />
              <span className="text-sm font-medium text-gray-900 dark:text-gray-100">AI Assistant</span>
            </div>
            <div className="mt-4 space-y-2">
              {(['explain', 'analyze', 'predict', 'summarize', 'recommend'] as AIAction[]).map((actionId) => {
                const action = AI_ACTIONS[actionId]
                return (
                  <button
                    key={actionId}
                    className="flex w-full items-center gap-2 rounded-lg px-3 py-2 text-sm text-gray-700 hover:bg-white dark:text-gray-300 dark:hover:bg-gray-800"
                  >
                    <Sparkles className="h-3.5 w-3.5 text-purple-500" />
                    {action.labelAr}
                  </button>
                )
              })}
            </div>
          </aside>
        )}
      </div>
    </div>
  )
}
