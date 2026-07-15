"use client"

import { useState } from "react"
import { useAskQuestion } from "@/lib/ragQueries"
import { RagChatView } from "./RagChatView"

interface Message {
  id: string
  role: "user" | "assistant"
  content: string
  citations?: { source: string; text: string; relevance: number }[]
  error?: boolean
}

export function RagChatContainer() {
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState("")
  const [expandedCitations, setExpandedCitations] = useState<string | null>(null)
  const askQuestion = useAskQuestion()

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
    <RagChatView
      messages={messages}
      input={input}
      setInput={setInput}
      expandedCitations={expandedCitations}
      setExpandedCitations={setExpandedCitations}
      isPending={askQuestion.isPending}
      onSend={handleSend}
      onRetry={handleRetry}
    />
  )
}
