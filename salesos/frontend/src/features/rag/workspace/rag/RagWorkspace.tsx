"use client"

import { RagChatWidget } from "../../widgets/rag-chat/RagChatWidget"
import { RagDocumentManager } from "../../widgets/rag-documents/RagDocumentManager"

export function RagWorkspace() {
  return (
    <div className="space-y-4">
      <h1 className="text-xl font-display text-[var(--text-primary)]">المساعد الذكي</h1>
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4" style={{ height: "calc(100vh - 12rem)" }}>
        <RagChatWidget />
        <RagDocumentManager />
      </div>
    </div>
  )
}
