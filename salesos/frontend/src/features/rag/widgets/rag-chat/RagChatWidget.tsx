"use client"

import { useState, useRef, useEffect } from "react"
import { useAskQuestion } from "@/lib/ragQueries"

interface Message {
  id: string
  role: "user" | "assistant"
  content: string
  citations?: { source: string; text: string; relevance: number }[]
  error?: boolean
}

export function RagChatWidget() {
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState("")
  const [expandedCitations, setExpandedCitations] = useState<string | null>(null)
  const askQuestion = useAskQuestion()
  const listRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    listRef.current?.scrollTo({ top: listRef.current.scrollHeight, behavior: "smooth" })
  }, [messages])

  const handleSend = async () => {
    if (!input.trim() || askQuestion.isPending) return
    const userMsg: Message = { id: crypto.randomUUID?.() || `${Date.now()}`, role: "user", content: input.trim() }
    setMessages((prev) => [...prev, userMsg])
    setInput("")

    try {
      const result = await askQuestion.mutateAsync(input.trim())
      const assistantMsg: Message = {
        id: crypto.randomUUID?.() || `${Date.now()}-res`,
        role: "assistant",
        content: result.answer,
        citations: result.citations,
      }
      setMessages((prev) => [...prev, assistantMsg])
    } catch {
      const errorMsg: Message = {
        id: crypto.randomUUID?.() || `${Date.now()}-err`,
        role: "assistant",
        content: "عذراً، حدث خطأ في الحصول على الإجابة",
        error: true,
      }
      setMessages((prev) => [...prev, errorMsg])
    }
  }

  const handleRetry = async (msg: Message) => {
    setMessages((prev) => prev.filter((m) => m.id !== msg.id))
    const lastUserMsg = [...messages].reverse().find((m) => m.role === "user")
    if (lastUserMsg) {
      setInput(lastUserMsg.content)
    }
  }

  return (
    <div className="flex h-full flex-col rounded-xl border border-[var(--border-default)] bg-[var(--bg-primary)] overflow-hidden">
      <div className="border-b border-[var(--border-default)] px-4 py-3">
        <h2 className="text-sm font-semibold text-[var(--text-primary)]">المساعد الذكي RAG</h2>
        <p className="text-xs text-[var(--text-muted)]">اسأل عن المستندات والبيانات</p>
      </div>

      <div ref={listRef} className="flex-1 overflow-auto space-y-3 p-4">
        {messages.length === 0 && (
          <div className="flex h-full items-center justify-center">
            <p className="text-sm text-[var(--text-muted)] text-center">اسأل سؤالاً للبدء</p>
          </div>
        )}

        {messages.map((msg) => (
          <div key={msg.id} className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}>
            <div className={`max-w-[80%] rounded-xl px-3 py-2 text-sm ${
              msg.role === "user"
                ? "bg-[var(--muhide-orange)] text-white"
                : msg.error
                  ? "bg-danger-50 text-danger-700 border border-danger-200"
                  : "bg-[var(--bg-secondary)] text-[var(--text-primary)]"
            }`}>
              <p className="whitespace-pre-wrap">{msg.content}</p>

              {msg.citations && msg.citations.length > 0 && (
                <div className="mt-2 border-t border-[var(--border-default)] pt-2">
                  <button
                    onClick={() => setExpandedCitations(expandedCitations === msg.id ? null : msg.id)}
                    className="text-xs text-[var(--text-muted)] hover:text-[var(--text-primary)]"
                  >
                    {expandedCitations === msg.id ? "إخفاء المصادر" : `${msg.citations.length} مصدر`}
                  </button>
                  {expandedCitations === msg.id && (
                    <div className="mt-1 space-y-1">
                      {msg.citations.map((c, i) => (
                        <div key={i} className="rounded bg-[var(--bg-primary)] p-2 text-xs text-[var(--text-secondary)]">
                          <p className="font-medium text-[var(--text-primary)]">{c.source}</p>
                          <p className="line-clamp-2">{c.text}</p>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}

              {msg.error && (
                <button onClick={() => handleRetry(msg)} className="mt-1 text-xs text-[var(--muhide-orange)] hover:underline">
                  إعادة المحاولة
                </button>
              )}
            </div>
          </div>
        ))}

        {askQuestion.isPending && (
          <div className="flex justify-start">
            <div className="rounded-xl bg-[var(--bg-secondary)] px-3 py-2 text-sm text-[var(--text-muted)]">
              <span className="animate-pulse">جاري البحث...</span>
            </div>
          </div>
        )}
      </div>

      <div className="border-t border-[var(--border-default)] p-3">
        <div className="flex items-center gap-2">
          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => { if (e.key === "Enter") handleSend() }}
            placeholder="اكتب سؤالك..."
            disabled={askQuestion.isPending}
            className="flex-1 rounded-lg border border-[var(--border-default)] bg-[var(--bg-primary)] px-3 py-2 text-sm text-[var(--text-primary)] placeholder:text-[var(--text-muted)] disabled:opacity-50"
          />
          <button
            onClick={handleSend}
            disabled={!input.trim() || askQuestion.isPending}
            className="rounded-lg bg-[var(--muhide-orange)] px-3 py-2 text-sm text-white hover:opacity-90 disabled:opacity-50"
          >
            إرسال
          </button>
        </div>
      </div>
    </div>
  )
}
