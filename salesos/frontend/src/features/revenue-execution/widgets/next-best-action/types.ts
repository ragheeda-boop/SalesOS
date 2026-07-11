import type { NextBestAction } from '@/application/revenue-execution/nba.dto'
export interface NBAViewProps { action: NextBestAction | null; onExecute?: (action: NextBestAction) => void }
