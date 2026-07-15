"use client"

import { DecisionProvider } from "@/features/revenue-execution/_providers/DecisionProvider"
import { RevenueWorkspace } from "@/features/revenue-execution/workspace/revenue/RevenueWorkspace"

export default function RevenuePage() {
  return (
    <DecisionProvider>
      <RevenueWorkspace />
    </DecisionProvider>
  )
}
