"use client";

import { FileText } from "lucide-react";
import { EmptyState } from "@salesos/ui";
import { asDocumentRows } from "./company360Lists";

export function Company360DocumentList({ documents }: { documents: unknown }) {
  const rows = asDocumentRows(documents);
  if (rows.length === 0) {
    return (
      <EmptyState
        icon={<FileText className="h-10 w-10" />}
        title="لا توجد وثائق"
        description="ستظهر المستندات والعقود المرتبطة بالشركة هنا"
      />
    );
  }
  return (
    <div className="space-y-3">
      {rows.map((doc) => (
        <div
          key={doc.id}
          className="flex items-center gap-3 p-3 rounded-lg border border-[var(--border-default)]"
        >
          <FileText className="h-8 w-8 text-[var(--muhide-orange)]/70" />
          <div>
            <div className="font-medium text-[var(--text-primary)]">{doc.name}</div>
            <div className="text-xs text-[var(--text-muted)]">
              {doc.type}
              {doc.date ? ` · ${doc.date}` : ""}
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}
