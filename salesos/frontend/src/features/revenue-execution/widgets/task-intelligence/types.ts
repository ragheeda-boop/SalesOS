import type { RevenueTask } from '@/application/revenue-execution/task.dto'
export interface TaskViewProps { tasks: RevenueTask[]; onComplete?: (id: string) => void }
