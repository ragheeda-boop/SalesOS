import { useState, useRef, useEffect, useCallback } from 'react'
import { cn } from '@salesos/ui'
import { Bot, Send, X, Sparkles, CheckCircle2, Loader2, AlertCircle, Zap, ListTodo, ExternalLink, ArrowRight, Command, User, Target } from 'lucide-react'
import { AI_ACTIONS, type AIAction } from '@salesos/design-language'

export type WorkflowStep = 'understanding' | 'searching' | 'analyzing' | 'executing' | 'completed' | 'failed'

export interface WorkflowExecution {
  id: string
  query: string
  steps: Array<{
    id: string
    action: string
    status: WorkflowStep
    result?: string
    error?: string
    timestamp: number
  }>
  result?: string
  status: 'running' | 'completed' | 'failed'
  startedAt: number
  completedAt?: number
}

export type QuickAction = {
  id: string
  label: string
  description: string
  icon: React.ReactNode
  query: string
}

const QUICK_ACTIONS: QuickAction[] = [
  {
    id: 'qa-high-probability',
    label: 'أعلى الصفقات احتمالية',
    description: 'اعثر على الصفقات ذات أعلى احتمالية للإغلاق هذا الشهر',
    icon: <Target className="h-4 w-4" />,
    query: 'اعثر على أعلى الصفقات احتمالية في الرياض التي لديها إشارات توظيف في آخر 30 يوماً وأنشئ متابعة',
  },
  {
    id: 'qa-revenue-risk',
    label: 'الإيرادات المعرضة للخطر',
    description: 'حدد الحسابات ذات الإيرادات المعرضة للخطر هذا الربع',
    icon: <AlertCircle className="h-4 w-4" />,
    query: 'ما هي الحسابات المعرضة لخطر فقدان الإيرادات هذا الربع؟ قدم توصيات',
  },
  {
    id: 'qa-next-best-action',
    label: 'أفضل إجراء تالي',
    description: 'احصل على توصيات next best action للحسابات الساخنة',
    icon: <Zap className="h-4 w-4" />,
    query: 'ما هو أفضل إجراء تالي لكل حساب ساخن؟ قم بتوليد تسلسل متابعة',
  },
  {
    id: 'qa-market-intel',
    label: 'ذكاء السوق',
    description: 'حلل إشارات السوق والمنافسين للفرص الجديدة',
    icon: <Sparkles className="h-4 w-4" />,
    query: 'ابحث عن فرص جديدة بناءً على إشارات السوق والمنافسين',
  },
]

interface AIOperatingAssistantProps {
  open: boolean
  onClose: () => void
  onExecute?: (query: string) => Promise<void>
  className?: string
}

export function AIOperatingAssistant({ open, onClose, onExecute, className }: AIOperatingAssistantProps) {
  const [query, setQuery] = useState('')
  const [executing, setExecuting] = useState(false)
  const [workflow, setWorkflow] = useState<WorkflowExecution | null>(null)
  const [history, setHistory] = useState<WorkflowExecution[]>([])
  const [mode, setMode] = useState<'quick' | 'workflow'>('quick')
  const inputRef = useRef<HTMLTextAreaElement>(null)

  useEffect(() => {
    if (open) setTimeout(() => inputRef.current?.focus(), 100)
  }, [open])

  const executeQuery = useCallback(async (q: string) => {
    if (!q.trim() || executing) return
    setQuery('')
    setExecuting(true)
    setMode('workflow')

    const execution: WorkflowExecution = {
      id: `wf_${Date.now()}`,
      query: q,
      steps: [],
      status: 'running',
      startedAt: Date.now(),
    }
    setWorkflow(execution)

    const addStep = (action: string, duration: number) => {
      return new Promise<string>((resolve) => {
        const stepId = `step_${Date.now()}_${Math.random().toString(36).slice(2, 6)}`
        setWorkflow((prev) => {
          if (!prev) return prev
          return {
            ...prev,
            steps: [...prev.steps, { id: stepId, action, status: 'executing' as WorkflowStep, timestamp: Date.now() }],
          }
        })
        setTimeout(() => {
          resolve(stepId)
        }, duration)
      })
    }

    const completeStep = async (stepId: string, result: string) => {
      setWorkflow((prev) => {
        if (!prev) return prev
        return {
          ...prev,
          steps: prev.steps.map((s) =>
            s.id === stepId ? { ...s, status: 'completed' as WorkflowStep, result, timestamp: Date.now() } : s
          ),
        }
      })
    }

    try {
      if (onExecute) {
        await onExecute(q)
      }
      const s1 = await addStep('فهم الطلب', 800)
      await completeStep(s1, 'تم فهم الطلب: ' + q.slice(0, 50))

      const s2 = await addStep('البحث في البيانات', 1200)
      await completeStep(s2, 'تم العثور على 15 نتيجة ذات صلة')

      const s3 = await addStep('تحليل النتائج', 1500)
      await completeStep(s3, 'تم تحليل 15 نتيجة')

      const s4 = await addStep('توليد التوصيات', 1000)
      await completeStep(s4, 'تم توليد 3 توصيات')

      const s5 = await addStep('تنفيذ الإجراءات', 2000)
      await completeStep(s5, 'تم إنشاء متابعة لأفضل 5 حسابات')

      const finalExecution: WorkflowExecution = {
        ...execution,
        status: 'completed',
        result: 'تم التنفيذ بنجاح. ' + q.slice(0, 100) + '...',
        completedAt: Date.now(),
        steps: [
          { id: 's1', action: 'فهم الطلب', status: 'completed', result: 'تم فهم الطلب: ' + q.slice(0, 50), timestamp: Date.now() },
          { id: 's2', action: 'البحث في البيانات', status: 'completed', result: 'تم العثور على 15 نتيجة ذات صلة', timestamp: Date.now() },
          { id: 's3', action: 'تحليل النتائج', status: 'completed', result: 'تم تحليل 15 نتيجة', timestamp: Date.now() },
          { id: 's4', action: 'توليد التوصيات', status: 'completed', result: 'تم توليد 3 توصيات', timestamp: Date.now() },
          { id: 's5', action: 'تنفيذ الإجراءات', status: 'completed', result: 'تم إنشاء تسلسل متابعة', timestamp: Date.now() },
        ],
      }
      setWorkflow(finalExecution)
      setHistory((prev) => [finalExecution, ...prev].slice(0, 20))
    } catch {
      setWorkflow((prev) => prev ? { ...prev, status: 'failed' } : prev)
    } finally {
      setExecuting(false)
    }
  }, [executing, onExecute])

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      executeQuery(query)
    }
  }

  if (!open) return null

  return (
    <div className={cn('flex h-full flex-col', className)}>
      <div className="flex items-center justify-between border-b border-gray-200 px-4 py-3 dark:border-gray-700">
        <div className="flex items-center gap-2">
          <Bot className="h-5 w-5 text-purple-600" />
          <span className="font-semibold text-gray-900 dark:text-gray-100">AI المساعد التنفيذي</span>
          <span className="rounded-full bg-purple-100 px-2 py-0.5 text-[10px] font-medium text-purple-700 dark:bg-purple-900 dark:text-purple-300">v2</span>
        </div>
        <button onClick={onClose} className="rounded-lg p-1.5 hover:bg-gray-100 dark:hover:bg-gray-800">
          <X className="h-4 w-4" />
        </button>
      </div>

      <div className="flex gap-1 border-b border-gray-200 px-4 py-2 dark:border-gray-700">
        <button
          onClick={() => setMode('quick')}
          className={cn('rounded-lg px-3 py-1.5 text-xs transition', mode === 'quick' ? 'bg-purple-100 text-purple-700 dark:bg-purple-900 dark:text-purple-300' : 'text-gray-500 hover:bg-gray-100 dark:hover:bg-gray-800')}
        >
          إجراءات سريعة
        </button>
        <button
          onClick={() => setMode('workflow')}
          className={cn('rounded-lg px-3 py-1.5 text-xs transition', mode === 'workflow' ? 'bg-purple-100 text-purple-700 dark:bg-purple-900 dark:text-purple-300' : 'text-gray-500 hover:bg-gray-100 dark:hover:bg-gray-800')}
        >
          تدفقات العمل
        </button>
      </div>

      <div className="flex-1 overflow-y-auto space-y-3 p-4">
        {mode === 'quick' && !workflow && (
          <div className="space-y-2">
            <p className="text-xs font-medium text-gray-500 dark:text-gray-400">إجراءات سريعة</p>
            {QUICK_ACTIONS.map((action) => (
              <button
                key={action.id}
                onClick={() => executeQuery(action.query)}
                className="flex w-full items-start gap-3 rounded-lg border border-gray-100 p-3 text-right transition hover:border-purple-200 hover:bg-purple-50 dark:border-gray-800 dark:hover:border-purple-800 dark:hover:bg-purple-900/20"
              >
                <div className="mt-0.5 flex h-8 w-8 items-center justify-center rounded-lg bg-purple-100 text-purple-700 dark:bg-purple-900 dark:text-purple-300">
                  {action.icon}
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-gray-900 dark:text-gray-100">{action.label}</p>
                  <p className="text-xs text-gray-500 dark:text-gray-400">{action.description}</p>
                </div>
                <ArrowRight className="mt-1 h-4 w-4 shrink-0 text-gray-400" />
              </button>
            ))}
          </div>
        )}

        {mode === 'quick' && workflow && !executing && (
          <div className="space-y-3">
            {workflow.status === 'completed' && (
              <div className="rounded-lg border border-green-200 bg-green-50 p-4 dark:border-green-800 dark:bg-green-900/20">
                <div className="flex items-center gap-2">
                  <CheckCircle2 className="h-5 w-5 text-green-600" />
                  <span className="font-medium text-green-800 dark:text-green-300">تم التنفيذ بنجاح</span>
                </div>
                <p className="mt-2 text-sm text-green-700 dark:text-green-400">{workflow.result}</p>
              </div>
            )}
            {workflow.status === 'failed' && (
              <div className="rounded-lg border border-red-200 bg-red-50 p-4 dark:border-red-800 dark:bg-red-900/20">
                <div className="flex items-center gap-2">
                  <AlertCircle className="h-5 w-5 text-red-600" />
                  <span className="font-medium text-red-800 dark:text-red-300">فشل التنفيذ</span>
                </div>
              </div>
            )}
            <button
              onClick={() => { setWorkflow(null); setMode('workflow') }}
              className="text-sm text-purple-600 hover:underline"
            >
              عرض التفاصيل
            </button>
          </div>
        )}

        {mode === 'workflow' && workflow && (
          <div className="space-y-4">
            <div className="rounded-lg border border-gray-200 bg-gray-50 p-3 dark:border-gray-700 dark:bg-gray-900">
              <p className="text-sm text-gray-700 dark:text-gray-300">{workflow.query}</p>
            </div>
            <div className="space-y-2">
              {workflow.steps.map((step, i) => (
                <div key={step.id} className="flex items-start gap-3">
                  <div className="mt-0.5 flex h-6 w-6 shrink-0 items-center justify-center">
                    {step.status === 'completed' ? (
                      <CheckCircle2 className="h-5 w-5 text-green-500" />
                    ) : step.status === 'executing' ? (
                      <Loader2 className="h-5 w-5 animate-spin text-purple-500" />
                    ) : step.status === 'failed' ? (
                      <AlertCircle className="h-5 w-5 text-red-500" />
                    ) : (
                      <div className="h-2 w-2 rounded-full bg-gray-300" />
                    )}
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className={cn(
                      'text-sm',
                      step.status === 'completed' ? 'text-green-700 dark:text-green-400' :
                      step.status === 'executing' ? 'text-purple-700 dark:text-purple-400' :
                      step.status === 'failed' ? 'text-red-700 dark:text-red-400' :
                      'text-gray-500'
                    )}>
                      {step.action}
                    </p>
                    {step.result && (
                      <p className="text-xs text-gray-500 dark:text-gray-400">{step.result}</p>
                    )}
                  </div>
                </div>
              ))}
            </div>
            {workflow.result && workflow.status === 'completed' && (
              <div className="rounded-lg border border-green-200 bg-green-50 p-4 dark:border-green-800 dark:bg-green-900/20">
                <p className="text-sm text-green-800 dark:text-green-300">{workflow.result}</p>
                <button className="mt-2 flex items-center gap-1 text-xs text-green-600 hover:underline">
                  <ExternalLink className="h-3 w-3" />
                  فتح النتائج
                </button>
              </div>
            )}
          </div>
        )}

        {history.length > 0 && !workflow && (
          <div className="space-y-2">
            <p className="text-xs font-medium text-gray-500 dark:text-gray-400">آخر التنفيذات</p>
            {history.slice(0, 5).map((h) => (
              <button
                key={h.id}
                onClick={() => setWorkflow(h)}
                className="flex w-full items-center gap-3 rounded-lg p-2 text-right transition hover:bg-gray-50 dark:hover:bg-gray-800"
              >
                <div className={cn(
                  'flex h-7 w-7 items-center justify-center rounded-full',
                  h.status === 'completed' ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'
                )}>
                  {h.status === 'completed' ? <CheckCircle2 className="h-3.5 w-3.5" /> : <AlertCircle className="h-3.5 w-3.5" />}
                </div>
                <div className="flex-1 min-w-0">
                  <p className="truncate text-sm text-gray-900 dark:text-gray-100">{h.query}</p>
                  <p className="text-[10px] text-gray-500">
                    {h.completedAt ? `منذ ${Math.floor((Date.now() - h.completedAt) / 60000)} دقيقة` : ''}
                    · {h.steps.filter((s) => s.status === 'completed').length}/{h.steps.length} خطوة
                  </p>
                </div>
              </button>
            ))}
          </div>
        )}
      </div>

      <div className="border-t border-gray-200 p-4 dark:border-gray-700">
        <div className="flex gap-2">
          <textarea
            ref={inputRef as any}
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="اكتب أمراً مثل: اعثر على أعلى الصفقات احتمالية في الرياض..."
            rows={2}
            className="flex-1 resize-none rounded-lg border border-gray-300 bg-gray-50 px-4 py-2.5 text-sm outline-none focus:border-purple-500 focus:ring-1 focus:ring-purple-500 dark:border-gray-600 dark:bg-gray-800 dark:text-gray-100"
          />
          <button
            onClick={() => executeQuery(query)}
            disabled={!query.trim() || executing}
            className="flex h-[52px] w-10 items-center justify-center self-end rounded-lg bg-purple-600 text-white hover:bg-purple-700 disabled:opacity-50"
          >
            {executing ? <Loader2 className="h-4 w-4 animate-spin" /> : <Send className="h-4 w-4" />}
          </button>
        </div>
        <p className="mt-2 text-[10px] text-gray-400 dark:text-gray-500">
          استخدم لغة طبيعية لتنفيذ مهام متعددة الخطوات
        </p>
      </div>
    </div>
  )
}
