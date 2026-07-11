import api from '@/lib/api'
import type { RevenueTask } from './task.dto'

export async function loadTasks(): Promise<RevenueTask[]> {
  try {
    const response = await api.get('/api/v1/revenue-execution/tasks')
    return response.data.items ?? response.data ?? []
  } catch {
    return []
  }
}

export async function saveTasks(tasks: RevenueTask[]): Promise<void> {
  try {
    await api.put('/api/v1/revenue-execution/tasks', tasks)
  } catch { /* ignore */ }
}

export async function addTask(task: Omit<RevenueTask, 'id' | 'createdAt'>): Promise<RevenueTask[]> {
  const response = await api.post('/api/v1/revenue-execution/tasks', task)
  const tasks = await loadTasks()
  return tasks
}

export async function completeTask(id: string): Promise<RevenueTask[]> {
  await api.patch(`/api/v1/revenue-execution/tasks/${id}/complete`)
  return loadTasks()
}

export async function getOverdueTasks(): Promise<RevenueTask[]> {
  const tasks = await loadTasks()
  return tasks.filter((t) => !t.completed && t.dueDate && new Date(t.dueDate) < new Date())
}

export async function getTasksByPriority(priority: string): Promise<RevenueTask[]> {
  const tasks = await loadTasks()
  return tasks.filter((t) => t.priority === priority && !t.completed)
}
