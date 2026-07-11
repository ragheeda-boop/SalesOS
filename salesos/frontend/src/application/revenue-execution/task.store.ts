import type { RevenueTask } from './task.dto'
import { createOpportunity, loadOpportunities } from './opportunity.store'

const TASK_KEY = 'salesos_tasks'

export function loadTasks(): RevenueTask[] {
  try { const s = localStorage.getItem(TASK_KEY); return s ? JSON.parse(s) : [] } catch { return [] }
}

export function saveTasks(tasks: RevenueTask[]): void {
  try { localStorage.setItem(TASK_KEY, JSON.stringify(tasks)) } catch { /* ignore */ }
}

export function addTask(task: Omit<RevenueTask, 'id' | 'createdAt'>): RevenueTask[] {
  const newTask: RevenueTask = { ...task, id: `task_${Date.now()}`, createdAt: new Date().toISOString() }
  const tasks = [newTask, ...loadTasks()]
  saveTasks(tasks)
  return tasks
}

export function completeTask(id: string): RevenueTask[] {
  const tasks = loadTasks().map((t) => t.id === id ? { ...t, completed: true } : t)
  saveTasks(tasks)
  return tasks
}

export function getOverdueTasks(): RevenueTask[] {
  return loadTasks().filter((t) => !t.completed && t.dueDate && new Date(t.dueDate) < new Date())
}

export function getTasksByPriority(priority: string): RevenueTask[] {
  return loadTasks().filter((t) => t.priority === priority && !t.completed)
}
