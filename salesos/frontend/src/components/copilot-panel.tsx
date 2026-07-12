"use client"

import { useState, useRef, useEffect } from "react"
import { cn } from "@salesos/ui"
import { Bot, Send, X, User, Sparkles, Loader2, PanelLeftClose, PanelLeftOpen, Maximize, Minimize } from "lucide-react"
import api from "@/lib/api"
import { getTenantId } from "@/lib/hooks/useTenant"

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

const INITIAL_MESSAGE: Message = {
  id: "welcome",
  role: "assistant",
  content: "مرحباً! أنا المساعد الذكي لـ SalesOS. يمكنني مساعدتك في تحليل البيانات والإجابة على أسئلتك.",
  timestamp: Date.now(),
}

export function CopilotPanel({ open, onClose, entityType, entityId, context }: CopilotPanelProps) {
  const [messages, setMessages] = useState<Message[]>(() => {
    if (typeof window === "undefined") return [INITIAL_MESSAGE]
    try {
      const saved = localStorage.getItem("salesos-copilot-messages")
      if (saved) {
        const parsed = JSON.parse(saved)
        if (Array.isArray(parsed) && parsed.length > 0) return parsed
      }
    } catch {}
    return [INITIAL_MESSAGE]
  })
  const [input, setInput] = useState("")
  const [loading, setLoading] = useState(false)
  const [mode, setMode] = useState<"collapsed" | "expanded" | "fullscreen">("expanded")
  const messagesEndRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }, [messages])

  useEffect(() => {
    if (messages.length > 1) {
      try {
        localStorage.setItem("salesos-copilot-messages", JSON.stringify(messages))
      } catch {}
    }
  }, [messages])

  useEffect(() => {
    if (!open) setMode("expanded")
  }, [open])

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape" && open) onClose()
    }
    document.addEventListener("keydown", handleKeyDown)
    return () => document.removeEventListener("keydown", handleKeyDown)
  }, [open, onClose])

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
      }, {
        headers: { "X-Tenant-Id": getTenantId() },
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

  const handleClearChat = () => {
    setMessages([INITIAL_MESSAGE])
    try { localStorage.removeItem("salesos-copilot-messages") } catch {}
  }

  if (!open) return null

  const isFullscreen = mode === "fullscreen"

  return (
    <div
      className={cn(
        "fixed z-50 flex flex-col bg-white shadow-muhide-6 dark:bg-neutral-900",
        isFullscreen
          ? "inset-0"
          : "bottom-8 w-[420px] max-w-[calc(100vw-2rem)] rounded-2xl border border-neutral-200 dark:border-neutral-700",
            !isFullscreen && "end-4",
        mode === "collapsed" && "h-auto"
      )}
      style={!isFullscreen ? { height: "560px", maxHeight: "calc(100vh - 4rem)" } : undefined}
      role="dialog"
      aria-label="المساعد الذكي"
    >
      <div className="flex h-12 items-center justify-between border-b px-4 shrink-0 dark:border-neutral-700">
        <div className="flex items-center gap-2">
          <Bot className="h-5 w-5 text-[var(--muhide-orange)]" />
          <span className="font-semibold text-sm text-neutral-900 dark:text-neutral-100">المساعد الذكي</span>
          <span className="rounded-full bg-info-100 px-1.5 py-0.5 text-[10px] font-medium text-info-700 dark:bg-info-900 dark:text-info-300">
            AI
          </span>
        </div>
        <div className="flex items-center gap-1">
          <button
            onClick={handleClearChat}
            className="rounded-lg p-1.5 text-[10px] text-neutral-400 hover:text-danger-500 hover:bg-neutral-100 dark:hover:bg-neutral-800"
            title="مسح المحادثة"
          >
            مسح
          </button>
          <button
            onClick={() => setMode(mode === "collapsed" ? "expanded" : "collapsed")}
            className="rounded-lg p-1.5 hover:bg-neutral-100 dark:hover:bg-neutral-800"
            aria-label={mode === "collapsed" ? "توسيع" : "طي"}
          >
            {mode === "collapsed" ? <PanelLeftOpen className="h-4 w-4" /> : <PanelLeftClose className="h-4 w-4" />}
          </button>
          <button
            onClick={() => setMode(mode === "fullscreen" ? "expanded" : "fullscreen")}
            className="rounded-lg p-1.5 hover:bg-neutral-100 dark:hover:bg-neutral-800"
            aria-label={mode === "fullscreen" ? "تصغير" : "ملء الشاشة"}
          >
            {mode === "fullscreen" ? <Minimize className="h-4 w-4" /> : <Maximize className="h-4 w-4" />}
          </button>
          <button onClick={onClose} className="rounded-lg p-1.5 hover:bg-neutral-100 dark:hover:bg-neutral-800">
            <X className="h-4 w-4" />
          </button>
        </div>
      </div>

      {mode !== "collapsed" && (
        <>
          <div className="flex-1 overflow-y-auto p-4 space-y-4">
            {messages.map((msg) => (
              <div
                key={msg.id}
                className={cn(
                  "flex gap-3",
                  msg.role === "user" ? "justify-end" : "justify-start"
                )}
              >
                <div
                  className={cn(
                    "flex h-8 w-8 shrink-0 items-center justify-center rounded-full",
                    msg.role === "user"
                      ? "order-last bg-info-100 text-info-700 dark:bg-info-900 dark:text-info-300"
                      : "bg-neutral-100 text-neutral-700 dark:bg-neutral-800 dark:text-neutral-300"
                  )}
                >
                  {msg.role === "user" ? <User className="h-4 w-4" /> : <Sparkles className="h-4 w-4" />}
                </div>
                <div
                  className={cn(
                    "max-w-[80%] rounded-xl px-4 py-2.5 text-sm leading-relaxed",
                    msg.role === "user"
                      ? "bg-[var(--muhide-orange)] text-white"
                      : "bg-neutral-100 text-neutral-900 dark:bg-neutral-800 dark:text-neutral-100"
                  )}
                >
                  {msg.content}
                </div>
              </div>
            ))}
            {loading && (
              <div className="flex items-center gap-2 text-sm text-neutral-500 ps-12">
                <Loader2 className="h-4 w-4 animate-spin" />
                جاري الكتابة...
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>
          <div className="border-t p-3 shrink-0 dark:border-neutral-700">
            <div className="flex gap-2">
              <input
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && !e.shiftKey && handleSend()}
                placeholder="اسأل المساعد الذكي..."
                className="flex-1 rounded-lg border border-neutral-300 bg-neutral-50 px-3 py-2.5 text-sm outline-none focus:border-[var(--muhide-orange)] focus:ring-1 focus:ring-[var(--muhide-orange)] dark:border-neutral-600 dark:bg-neutral-800 dark:text-neutral-100"
              />
              <button
                onClick={handleSend}
                disabled={!input.trim() || loading}
                className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-[var(--muhide-orange)] text-white hover:bg-orange-700 disabled:opacity-50"
              >
                <Send className="h-4 w-4" />
              </button>
            </div>
            <p className="mt-2 text-center text-[10px] text-neutral-400">
              اضغط Enter للإرسال
            </p>
          </div>
        </>
      )}
    </div>
  )
}
