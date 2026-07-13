"use client"

import { useParams } from "next/navigation"
import { OpportunityWorkspace } from "@/features/revenue-execution/workspace/OpportunityWorkspace"

export default function OpportunityDetailPage() {
  const { id } = useParams<{ id: string }>()
  return <OpportunityWorkspace opportunityId={id} />
}
