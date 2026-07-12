"use client";

import { useState, type DragEvent } from "react";
import { cn, Badge } from "@salesos/ui";
import type { Opportunity } from "@/lib/api";
import { OpportunityCard } from "./OpportunityCard";

export function PipelineColumn({
  stage,
  opportunities,
  onDrop,
}: {
  stage: { key: string; label: string; color: string };
  opportunities: Opportunity[];
  onDrop: (oppId: string, toStage: string) => void;
}) {
  const [dragOver, setDragOver] = useState(false);

  const handleDragOver = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setDragOver(true);
  };

  const handleDragLeave = () => setDragOver(false);

  const handleDrop = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setDragOver(false);
    const oppId = e.dataTransfer.getData("text/plain");
    if (oppId) onDrop(oppId, stage.key);
  };

  return (
    <div
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
      className={cn(
        "flex w-[260px] shrink-0 flex-col rounded-xl border border-neutral-200 bg-neutral-50/80",
        dragOver && "border-[var(--muhide-orange)]/50 bg-[var(--muhide-orange)]/10"
      )}
    >
      <div className="flex items-center gap-2 border-b border-neutral-200 px-3 py-2.5">
        <span className={cn("h-2.5 w-2.5 rounded-full", stage.color)} />
        <span className="text-sm font-semibold text-neutral-800">{stage.label}</span>
        <Badge variant="outline" className="mr-auto text-xs">
          {opportunities.length}
        </Badge>
      </div>
      <div className="flex flex-col gap-2 p-2 overflow-y-auto max-h-[calc(100vh-280px)]">
        {opportunities.map((opp) => (
          <OpportunityCard key={opp.id} opportunity={opp} />
        ))}
        {opportunities.length === 0 && (
          <p className="py-8 text-center text-xs text-neutral-400">
            اسحب الفرصة هنا
          </p>
        )}
      </div>
    </div>
  );
}
