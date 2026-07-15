"use client"

import { DecisionProvider } from "@/features/revenue-execution/_providers/DecisionProvider"
import { PipelineWorkspace } from "@/features/revenue-execution/workspace/pipeline/PipelineWorkspace"

export default function PipelinePage() {
  return (
    <DecisionProvider>
      <PipelineWorkspace />
    </DecisionProvider>
  )
}
