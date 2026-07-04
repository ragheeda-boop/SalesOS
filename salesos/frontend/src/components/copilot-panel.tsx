"use client"

import { useState, useRef, useEffect } from "react"
import { cn } from "@salesos/ui"
import { Bot, Send, X, User, Sparkles, Loader2 } from "lucide-react"
import api from "@/lib/api"

interface Message {
  id: string
  role: "user" | "assistant"
  content: string
  timestamp: number
}

interface CopilotPanelProps {
  open: boolean
  onClose: () => void
  entityType?: string
  entityId?: string
  context?: Record<string, unknown>
}

export function CopilotPanel({ open, onClose, entityType, entityId, context }: CopilotPanelProps) {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: "welcome",
      role: "assistant",
      content: entityType
        ? `مرحباً! كيف يمكنني مساعدتك في تحليل ${entityType === "company" ? "هذه الشركة" : "هذه البيانات"}؟`
        : "مرحباً! أنا المساعد الذكي لـ SalesOS. يمكنني مساعدتك في تحليل البيانات والإجابة على أسئلتك.",
      timestamp: Date.now(),
    },
  ])
  const [input, setInput] = useState("")
  const [loading, setLoading] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }, [messages])

  const handleSend = async () => {
    if (!input.trim() || loading) return

    const userMsg: Message = {
      id: `user_${Date.now()}`,
      role: "user",
      content: input.trim(),
      timestamp: Date.now(),
    }

    setMessages((prev) => [...prev, userMsg])
    setInput("")
    setLoading(true)

    try {
      const res = await api.post("/api/v1/copilot/query", {
        query: input.trim(),
        company_id: entityId,
        company_name: context?.company_name || undefined,
        cr_number: context?.cr_number || undefined,
        city: context?.city || undefined,
        goal: context?.goal || undefined,
      })

      const data = res.data
      setMessages((prev) => [
        ...prev,
        {
          id: `assistant_${Date.now()}`,
          role: "assistant",
          content: data.response || "لم يتم العثور على رد.",
          timestamp: Date.now(),
        },
      ])
    } catch {
      setMessages((prev) => [
        ...prev,
        {
          id: `assistant_${Date.now()}`,
          role: "assistant",
          content: "عذراً، حدث خطأ في الاتصال بالمساعد الذكي. يرجى التحقق من اتصال الخادم.",
          timestamp: Date.now(),
        },
      ])
    } finally {
      setLoading(false)
    }
  }

  if (!open) return null

  return (
    <div className="fixed inset-y-0 left-0 z-40 flex w-96 flex-col border-l bg-white shadow-xl dark:border-gray-700 dark:bg-gray-900">
      <div className="flex h-14 items-center justify-between border-b px-4 dark:border-gray-700">
        <div className="flex items-center gap-2">
          <Bot className="h-5 w-5 text-blue-600" />
          <span className="font-semibold text-gray-900 dark:text-gray-100">المساعد الذكي</span>
          <span className="rounded-full bg-blue-100 px-2 py-0.5 text-[10px] font-medium text-blue-700 dark:bg-blue-900 dark:text-blue-300">
            AI
          </span>
        </div>
        <button onClick={onClose} className="rounded-lg p-1.5 hover:bg-gray-100 dark:hover:bg-gray-800">
          <X className="h-5 w-5" />
        </button>
      </div>
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.map((msg) => (
          <div
            key={msg.id}
            className={cn(
              "flex gap-3",
              msg.role === "user" ? "flex-row-reverse" : "flex-row"
            )}
          >
            <div
              className={cn(
                "flex h-8 w-8 shrink-0 items-center justify-center rounded-full",
                msg.role === "user"
                  ? "bg-blue-100 text-blue-700 dark:bg-blue-900 dark:text-blue-300"
                  : "bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-300"
              )}
            >
              {msg.role === "user" ? <User className="h-4 w-4" /> : <Sparkles className="h-4 w-4" />}
            </div>
            <div
              className={cn(
                "max-w-[80%] rounded-xl px-4 py-2.5 text-sm leading-relaxed",
                msg.role === "user"
                  ? "bg-blue-600 text-white"
                  : "bg-gray-100 text-gray-900 dark:bg-gray-800 dark:text-gray-100"
              )}
            >
              {msg.content}
            </div>
          </div>
        ))}
        <div ref={messagesEndRef} />
      </div>
      <div className="border-t p-4 dark:border-gray-700">
        <div className="flex gap-2">
          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && !e.shiftKey && handleSend()}
            placeholder="اسأل المساعد الذكي..."
            className="flex-1 rounded-lg border border-gray-300 bg-gray-50 px-4 py-2.5 text-sm outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-800 dark:text-gray-100"
          />
          <button
            onClick={handleSend}
            disabled={!input.trim() || loading}
            className="flex h-10 w-10 items-center justify-center rounded-lg bg-blue-600 text-white hover:bg-blue-700 disabled:opacity-50"
          >
            <Send className="h-4 w-4" />
          </button>
        </div>
      </div>
    </div>
  )
}
