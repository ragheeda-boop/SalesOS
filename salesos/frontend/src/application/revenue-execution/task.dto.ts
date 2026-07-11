export type TaskPriority = 'critical' | 'high' | 'medium' | 'low'

export interface RevenueTask {
  id: string
  title: string
  description?: string
  priority: TaskPriority
  source: 'nba' | 'meeting' | 'email' | 'manual' | 'signal'
  sourceEntityId?: string
  companyId?: string
  companyName?: string
  assignee?: string
  dueDate?: string
  completed: boolean
  createdAt: string
}

export interface TaskInsight {
  tasks: RevenueTask[]
  total: number
  completed: number
  overdue: number
  criticalCount: number
  byPriority: Record<TaskPriority, number>
}
