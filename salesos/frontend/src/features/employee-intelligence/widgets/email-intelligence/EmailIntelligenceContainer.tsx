'use client'

import { EmailIntelligenceView } from './EmailIntelligenceView'
import type { EmailIntelligence } from '@/lib/api'

export function EmailIntelligenceContainer({ data }: { data: EmailIntelligence }) {
  return <EmailIntelligenceView data={data} />
}
