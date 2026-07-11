export interface EmailSummary {
  threadId: string
  subject: string
  summary: string
  sender: string
  date: string
  priority: 'low' | 'medium' | 'high'
  suggestedReply?: string
  relatesTo?: { entityType: string; entityId: string; entityName: string }
  actionItems: string[]
}
