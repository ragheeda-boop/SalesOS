import { loadTasks, saveTasks, addTask, completeTask, getOverdueTasks, getTasksByPriority } from '../task.store'

describe('task store', () => {
  beforeEach(() => {
    localStorage.clear()
    jest.useFakeTimers()
    jest.setSystemTime(new Date('2026-07-11T12:00:00Z'))
  })

  afterEach(() => {
    jest.useRealTimers()
  })

  describe('loadTasks / saveTasks', () => {
    it('returns empty array when no tasks stored', () => {
      expect(loadTasks()).toEqual([])
    })

    it('saves and loads tasks', () => {
      const tasks = [{ id: 't-1', title: 'Test', priority: 'high' as const, source: 'manual' as const, completed: false, createdAt: '2026-07-10T10:00:00Z' }]
      saveTasks(tasks)
      expect(loadTasks()).toEqual(tasks)
    })

    it('returns empty array on corrupt localStorage', () => {
      localStorage.setItem('salesos_tasks', '{corrupt}')
      expect(loadTasks()).toEqual([])
    })
  })

  describe('addTask', () => {
    it('adds a task with generated id and createdAt', () => {
      const tasks = addTask({ title: 'Follow up', priority: 'high', source: 'nba', companyId: 'c-1', completed: false })
      expect(tasks).toHaveLength(1)
      expect(tasks[0].id).toContain('task_')
      expect(tasks[0].createdAt).toBe('2026-07-11T12:00:00.000Z')
      expect(tasks[0].title).toBe('Follow up')
      expect(tasks[0].completed).toBe(false)
    })

    it('prepends new tasks to existing ones', () => {
      addTask({ title: 'First', priority: 'high', source: 'manual', completed: false })
      addTask({ title: 'Second', priority: 'low', source: 'manual', completed: false })

      const all = loadTasks()
      expect(all).toHaveLength(2)
      expect(all[0].title).toBe('Second')
    })
  })

  describe('completeTask', () => {
    it('marks a task as completed', () => {
      addTask({ title: 'Task', priority: 'medium', source: 'manual', completed: false })
      const task = loadTasks()[0]
      const updated = completeTask(task.id)
      expect(updated[0].completed).toBe(true)
    })
  })

  describe('getOverdueTasks', () => {
    it('returns tasks with dueDate in the past', () => {
      addTask({ title: 'Overdue', priority: 'high', source: 'manual', completed: false, dueDate: '2026-07-10T12:00:00Z' })
      addTask({ title: 'Future', priority: 'low', source: 'manual', completed: false, dueDate: '2026-07-20T12:00:00Z' })

      const overdue = getOverdueTasks()
      expect(overdue).toHaveLength(1)
      expect(overdue[0].title).toBe('Overdue')
    })
  })

  describe('getTasksByPriority', () => {
    it('filters tasks by priority', () => {
      addTask({ title: 'Critical 1', priority: 'critical', source: 'nba', completed: false })
      addTask({ title: 'Critical 2', priority: 'critical', source: 'nba', completed: false })
      addTask({ title: 'Low', priority: 'low', source: 'manual', completed: false })

      expect(getTasksByPriority('critical')).toHaveLength(2)
      expect(getTasksByPriority('low')).toHaveLength(1)
      expect(getTasksByPriority('high')).toHaveLength(0)
    })
  })
})
