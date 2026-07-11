export interface SignalItemData {
  id: string
  companyId: string
  companyName: string
  category: 'tender' | 'regulatory' | 'competitor' | 'financial' | 'news'
  title: string
  summary: string
  severity: 'low' | 'medium' | 'high' | 'critical'
  source: string
  timestamp: string
  isUnseen: boolean
}

export interface IntelligenceFeedViewProps {
  items: SignalItemData[]
  total: number
  unseenCount: number
  onItemClick?: (id: string) => void
  onShowAll?: () => void
}
