'use client'

import type { ReactNode } from 'react'
import { DecisionProvider } from '../_providers/DecisionProvider'

export function RevenueExecutionLayout({ children }: { children: ReactNode }) {
 return <DecisionProvider>{children}</DecisionProvider>
}
