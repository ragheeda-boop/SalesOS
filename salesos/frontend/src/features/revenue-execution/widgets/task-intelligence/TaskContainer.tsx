'use client'

import { createWidget } from '@salesos/workspace'
import { loadTasks, completeTask } from '@/application/revenue-execution/task.store'

export const TaskIntelligenceWidget = createWidget({
  metadata: { id: 'taskIntelligence', title: 'المهام', category: 'intelligence', priority: 'high', permissions: ['task:read'], featureFlag: { enabled: true }, minHeight: '360px' },
  useData: () => {
    const tasks = loadTasks()
    return { data: tasks, status: 'ready' as const, lastUpdated: new Date().toISOString(), error: null, refetch: () => {} }
  },
  render: ({ data }) => <TaskView tasks={data} onComplete={(id) => { completeTask(id) }} />,
})
