"use client";

import { useParams } from "next/navigation";
import { DecisionProvider } from "@/features/revenue-execution/_providers/DecisionProvider";
import { OpportunityWorkspace } from "@/features/revenue-execution/workspace/OpportunityWorkspace";
import { CustomFieldsAutoRender } from "@/features/tenant-studio/CustomFieldsAutoRender";

export default function OpportunityDetailPage() {
  const { id } = useParams<{ id: string }>();
  return (
    <DecisionProvider>
      <div className="space-y-6">
        <OpportunityWorkspace opportunityId={id} />
        <CustomFieldsAutoRender objectKey="opportunity" />
      </div>
    </DecisionProvider>
  );
}
