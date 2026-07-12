"use client";

import { useState, type DragEvent } from "react";
import { Building2 } from "lucide-react";
import { cn, Badge } from "@salesos/ui";
import type { Opportunity } from "@/lib/api";

function formatCurrency(value: number): string {
  if (value >= 1_000_000) return `${(value / 1_000_000).toFixed(1)}M`;
  if (value >= 1_000) return `${(value / 1_000).toFixed(0)}K`;
  return value.toLocaleString();
}

export function OpportunityCard({
  opportunity,
}: {
  opportunity: Opportunity;
}) {
  const [dragging, setDragging] = useState(false);

  const handleDragStart = (e: DragEvent<HTMLDivElement>) => {
    e.dataTransfer.setData("text/plain", opportunity.id);
    setDragging(true);
  };

  const handleDragEnd = () => setDragging(false);

  return (
    <div
      draggable
      onDragStart={handleDragStart}
      onDragEnd={handleDragEnd}
      className={cn(
        "cursor-grab rounded-lg border border-neutral-200 bg-white p-3 shadow-muhide-1 transition-all hover:shadow-muhide-3 active:cursor-grabbing",
        dragging && "opacity-50 ring-2 ring-[var(--muhide-orange)]/50"
      )}
    >
      <div className="mb-1 flex items-start justify-between gap-2">
        <h4 className="text-sm font-medium text-neutral-900 leading-snug">
          {opportunity.name}
        </h4>
        <span className="shrink-0 text-sm font-semibold text-neutral-700">
          {formatCurrency(opportunity.value)} SAR
        </span>
      </div>
      {opportunity.company_name && (
        <div className="flex items-center gap-1 text-xs text-neutral-500">
          <Building2 className="h-3 w-3" />
          <span>{opportunity.company_name}</span>
        </div>
      )}
      {opportunity.status === "won" && opportunity.won_amount != null && (
        <Badge variant="success" className="mt-1 text-xs">
          {formatCurrency(opportunity.won_amount)} SAR
        </Badge>
      )}
      {opportunity.status === "lost" && opportunity.loss_reason && (
        <p className="mt-1 text-xs text-danger-500">{opportunity.loss_reason}</p>
      )}
    </div>
  );
}
