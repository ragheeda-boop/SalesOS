"use client"

import { NBAWidgetContainer } from"./NBAWidgetContainer"

interface NBAWidgetProps {
 opportunityId: string
}

export function NBAWidget({ opportunityId }: NBAWidgetProps) {
 return <NBAWidgetContainer opportunityId={opportunityId} />
}
