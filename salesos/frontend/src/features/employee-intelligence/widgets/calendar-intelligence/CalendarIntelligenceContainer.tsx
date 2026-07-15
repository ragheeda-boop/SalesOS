'use client'

import { CalendarIntelligenceView } from './CalendarIntelligenceView'
import type { CalendarIntelligence } from '@/lib/api'

export function CalendarIntelligenceContainer({ data }: { data: CalendarIntelligence }) {
  return <CalendarIntelligenceView data={data} />
}
