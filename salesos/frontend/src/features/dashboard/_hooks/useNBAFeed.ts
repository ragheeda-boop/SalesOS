import { useMemo } from 'react'
import type { NBAFeedItem } from '../sdk/types'

export function useNBAFeed(): NBAFeedItem[] {
  return useMemo(() => [], [])
}
