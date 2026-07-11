'use client'

import { useCallback } from 'react'
import { createWidget } from '@salesos/workspace'
import { useTasks, useCompleteTask } from '@/lib/hooks/taskQueries'
import type { RevenueTask } from '@/application/revenue-execution/task.dto'

export const TaskIntelligenceWidget = createWidget({
  metadata: { id: 'taskIntelligence', title: 'المهام', category: 'intelligence', priority: 'high', permissions: ['task:read'], featureFlag: { enabled: true }, minHeight: '360px' },
  useData: () => {
    const { data: tasksData, isLoading, error, refetch } = useTasks()
    const { mutate: completeTaskMutate } = useCompleteTask()

    const tasks: RevenueTask[] = (tasksData ?? []).map((t) => ({
      id: t.id,
      title: t.title,
      priority: t.priority as RevenueTask['priority'],
      source: t.source as RevenueTask['source'],
      companyId: t.company_id ?? undefined,
      completed: t.completed,
      createdAt: t.created_at ?? '',
    }))

    const handleComplete = useCallback((id: string) => {
      completeTaskMutate({ taskId: id })
    }, [completeTaskMutate])

    return {
      data: tasks,
      status: isLoading ? 'loading' : 'ready',
      lastUpdated: new Date().toISOString(),
      error,
      refetch,
      onComplete: handleComplete,
    }
  },
  render: ({ data, onComplete }) => <TaskView tasks={data} onComplete={onComplete} />,
})
