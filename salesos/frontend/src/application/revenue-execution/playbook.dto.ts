export interface PlaybookStep {
  id: string
  order: number
  title: string
  description: string
  duration: string
}

export interface Playbook {
  id: string
  name: string
  description: string
  industry: string
  steps: PlaybookStep[]
  estimatedDuration: string
  successRate: number
}
