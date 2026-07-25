"use client"

import { useState, useRef, useEffect, useCallback } from"react"
import { cn, Spinner } from"@salesos/ui"
import {
 Bot, Send, X, User, Sparkles,
 PanelLeftClose, PanelLeftOpen,
 Maximize, Minimize, GitBranch,
 ThumbsUp, ThumbsDown, MessageSquare,
} from"lucide-react"
import api from"@/lib/api"
import { getTenantId } from"@/lib/hooks/useTenant"
import { useTranslation } from"@/lib/i18n"

interface FeedbackState {
 rating:"positive" |"negative" | null
 comment: string
 submitted: boolean
}

interface Message {
 id: string
 role:"user" |"assistant"
 content: string
 timestamp: number
 parentId: string | null
 branchId: string
 feedback?: FeedbackState
 aggregateFeedback?: { positive: number; negative: number; total: number }
}

interface Branch {
 id: string
 label: string
 parentMessageId: string
}

interface CopilotPanelProps {
 open: boolean
 onClose: () => void
 entityType?: string
 entityId?: string
 context?: Record<string, unknown>
 embedded?: boolean
}

const INITIAL_MESSAGE: Message = {
 id:"welcome",
 role:"assistant",
 content:"",
 timestamp: Date.now(),
 parentId: null,
 branchId:"main",
}

export function CopilotPanel({ open, onClose, entityType, entityId, context, embedded = false }: CopilotPanelProps) {
 const { t } = useTranslation()
 const [messages, setMessages] = useState<Message[]>([{
 ...INITIAL_MESSAGE,
 content: t("copilot.welcome"),
 }])
 const [branches, setBranches] = useState<Branch[]>([])
 const [activeBranchId, setActiveBranchId] = useState("main")
 const [input, setInput] = useState("")
 const [loading, setLoading] = useState(false)
 const [mode, setMode] = useState<"collapsed" |"expanded" |"fullscreen">("expanded")
 const [feedbackTarget, setFeedbackTarget] = useState<string | null>(null)
 const messagesEndRef = useRef<HTMLDivElement>(null)

 const getVisibleMessages = useCallback(() => {
 return messages.filter((m) => {
 if (m.branchId ==="main") return true
 return m.branchId === activeBranchId
 }).filter((m, _idx, arr) => {
 if (m.branchId ==="main") return true
 const branchMessages = arr.filter((a) => a.branchId === m.branchId)
 if (branchMessages.length === 0) return true
 const lastBranchMsg = branchMessages[branchMessages.length - 1]
 return arr.findIndex((a) => a.id === m.id) <= arr.findIndex((a) => a.id === lastBranchMsg.id)
 })
 }, [messages, activeBranchId])

 const visibleMessages = getVisibleMessages()

 useEffect(() => {
 messagesEndRef.current?.scrollIntoView({ behavior:"smooth" })
 }, [visibleMessages])

 useEffect(() => {
 if (!open) setMode("expanded")
 }, [open])

 useEffect(() => {
 const handleKeyDown = (e: KeyboardEvent) => {
 if (e.key ==="Escape" && open) onClose()
 }
 document.addEventListener("keydown", handleKeyDown)
 return () => document.removeEventListener("keydown", handleKeyDown)
 }, [open, onClose])

 const handleSend = async () => {
 if (!input.trim() || loading) return

 const userMsg: Message = {
 id: `user_${Date.now()}`,
 role:"user",
 content: input.trim(),
 timestamp: Date.now(),
 parentId: null,
 branchId: activeBranchId,
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
 headers: {"X-Tenant-Id": getTenantId() },
 })

 const data = res.data
 setMessages((prev) => [
 ...prev,
 {
 id: `assistant_${Date.now()}`,
 role:"assistant",
 content: data.response || t("copilot.no_response"),
 timestamp: Date.now(),
 parentId: userMsg.id,
 branchId: userMsg.branchId,
 aggregateFeedback: data.feedback_summary || undefined,
 },
 ])
 } catch {
 setMessages((prev) => [
 ...prev,
 {
 id: `assistant_${Date.now()}`,
 role:"assistant",
 content: t("copilot.connection_error"),
 timestamp: Date.now(),
 parentId: userMsg.id,
 branchId: userMsg.branchId,
 },
 ])
 } finally {
 setLoading(false)
 }
 }

 const handleBranch = (fromMessageId: string) => {
 const branchNum = branches.filter((b) => b.parentMessageId === fromMessageId).length + 1
 const newBranchId = `branch_${fromMessageId}_${branchNum}`
 setBranches((prev) => [...prev, {
 id: newBranchId,
 label: t("copilot.branch_alt", { n: String(branchNum) }),
 parentMessageId: fromMessageId,
 }])
 setActiveBranchId(newBranchId)
 }

 const handleFeedback = async (messageId: string, rating:"positive" |"negative") => {
 setMessages((prev) => prev.map((m) =>
 m.id === messageId
 ? { ...m, feedback: { rating, comment:"", submitted: false } }
 : m
 ))
 setFeedbackTarget(messageId)
 }

 const submitFeedback = async (messageId: string, comment?: string) => {
 try {
 await api.post("/api/v1/copilot/feedback", {
 message_id: messageId,
 rating: messages.find((m) => m.id === messageId)?.feedback?.rating,
 comment: comment || undefined,
 }, {
 headers: {"X-Tenant-Id": getTenantId() },
 })
 } catch { /* best-effort */ }

 setMessages((prev) => prev.map((m) =>
 m.id === messageId
 ? { ...m, feedback: { ...m.feedback!, submitted: true } }
 : m
 ))
 setFeedbackTarget(null)
 }

 const handleClearChat = () => {
 setMessages([{ ...INITIAL_MESSAGE, content: t("copilot.welcome") }])
 setBranches([])
 setActiveBranchId("main")
 }

 if (!open) return null

 const isFullscreen = mode ==="fullscreen"

 return (
 <div
 className={cn(
 embedded
 ?"flex flex-col h-full bg-[var(--bg-primary)] rounded-2xl border border-[var(--border-default)]"
 :"fixed z-50 flex flex-col bg-[var(--bg-primary)] shadow-muhide-6",
 !embedded && isFullscreen &&"inset-0",
 !embedded && !isFullscreen &&"bottom-8 w-[420px] max-w-[calc(100vw-2rem)] rounded-2xl border border-[var(--border-default)]",
 !embedded && !isFullscreen &&"end-4",
 !embedded && mode ==="collapsed" &&"h-auto"
 )}
 style={!embedded && !isFullscreen ? { height:"560px", maxHeight:"calc(100vh - 4rem)" } : undefined}
 role="dialog"
 aria-label={t("copilot.title")}
 >
 <div className="flex h-12 items-center justify-between border-b px-4 shrink-0">
 <div className="flex items-center gap-2">
 <Bot className="h-5 w-5 text-[var(--muhide-orange)]" />
 <span className="font-semibold text-sm text-[var(--text-primary)]">{t("copilot.title")}</span>
 <span className="rounded-full bg-info-100 px-1.5 py-0.5 text-[10px] font-medium text-info-700 dark:bg-info-900 dark:text-info-300">
 AI
 </span>
 {branches.length > 0 && (
          <span className="flex items-center gap-1 rounded-full bg-[var(--chart-purple-bg)] px-1.5 py-0.5 text-[10px] font-medium text-[var(--text-secondary)] dark:bg-[var(--bg-primary)] dark:text-[var(--text-muted)]">
 <GitBranch className="h-3 w-3" />
 {branches.length}
 </span>
 )}
 </div>
 <div className="flex items-center gap-1">
 <button
 onClick={handleClearChat}
 className="rounded-lg p-1.5 text-[10px] text-[var(--text-disabled)] hover:text-danger-500 hover:bg-[var(--bg-tertiary)] dark:hover:bg-[var(--bg-secondary)]"
 title={t("copilot.clear")}
 >
 {t("copilot.clear")}
 </button>
 <button
 onClick={() => setMode(mode ==="collapsed" ?"expanded" :"collapsed")}
 className="rounded-lg p-1.5 hover:bg-[var(--bg-tertiary)] dark:hover:bg-[var(--bg-secondary)]"
 aria-label={mode ==="collapsed" ? t("a11y.expand") : t("a11y.collapse")}
 >
 {mode ==="collapsed" ? <PanelLeftOpen className="h-4 w-4" /> : <PanelLeftClose className="h-4 w-4" />}
 </button>
 <button
 onClick={() => setMode(mode ==="fullscreen" ?"expanded" :"fullscreen")}
 className="rounded-lg p-1.5 hover:bg-[var(--bg-tertiary)] dark:hover:bg-[var(--bg-secondary)]"
 aria-label={mode ==="fullscreen" ? t("a11y.minimize") : t("a11y.fullscreen")}
 >
 {mode ==="fullscreen" ? <Minimize className="h-4 w-4" /> : <Maximize className="h-4 w-4" />}
 </button>
 {!embedded && (
 <button onClick={onClose} className="rounded-lg p-1.5 hover:bg-[var(--bg-tertiary)] dark:hover:bg-[var(--bg-secondary)]">
 <X className="h-4 w-4" />
 </button>
 )}
 </div>
 </div>

 {mode !=="collapsed" && (
 <>
 <div className="flex-1 overflow-y-auto p-4 space-y-4">
 {visibleMessages.map((msg) => (
 <div key={msg.id} className="relative group">
 {msg.branchId !=="main" && (
                <div className="absolute -start-3 top-0 bottom-0 w-0.5 bg-[var(--chart-purple-bg)] dark:bg-[var(--bg-secondary)] rounded-full" />
 )}
 {msg.branchId !=="main" && msg.role ==="user" && (
                <div className="absolute -start-4 top-3 h-2 w-2 rounded-full bg-[var(--chart-purple)] border-2 border-white" />
 )}
 <div className={cn("flex gap-3", msg.role ==="user" ?"justify-end" :"justify-start")}>
 <div
 className={cn(
"flex h-8 w-8 shrink-0 items-center justify-center rounded-full",
 msg.role ==="user"
 ?"order-last bg-info-100 text-info-700 dark:bg-info-900 dark:text-info-300"
 :"bg-[var(--bg-tertiary)] text-[var(--text-secondary)]"
 )}
 >
 {msg.role ==="user" ? <User className="h-4 w-4" /> : <Sparkles className="h-4 w-4" />}
 </div>
 <div className="max-w-[80%] space-y-1">
 <div
 className={cn(
"rounded-xl px-4 py-2.5 text-sm leading-relaxed",
 msg.role ==="user"
 ?"bg-[var(--muhide-orange)] text-white"
 :"bg-[var(--bg-tertiary)] text-[var(--text-primary)]"
 )}
 >
 {msg.content}
 </div>

 {msg.role ==="assistant" && !loading && (
 <div className="flex items-center gap-1.5 px-1">
 <FeedbackButtons
 msg={msg}
 onFeedback={handleFeedback}
 onSubmit={submitFeedback}
 feedbackTarget={feedbackTarget}
 setFeedbackTarget={setFeedbackTarget}
 t={t}
 />
 <button
 onClick={() => handleBranch(msg.id)}
                className="rounded-md p-1 text-[var(--text-disabled)] hover:text-[var(--chart-purple)] hover:bg-[var(--chart-purple-bg)] dark:hover:bg-[var(--bg-primary)]/30 transition-colors opacity-0 group-hover:opacity-100"
 title={t("copilot.branch_from")}
 aria-label={t("copilot.branch_from")}
 >
 <GitBranch className="h-3.5 w-3.5" />
 </button>
 </div>
 )}
 </div>
 </div>
 </div>
 ))}
 {loading && (
 <div className="flex items-center gap-2 text-sm text-[var(--text-muted)] ps-12">
 <Spinner className="h-4 w-4" />
 {t("copilot.typing")}
 </div>
 )}
 <div ref={messagesEndRef} />
 </div>

 {branches.length > 0 && (
 <div className="border-t px-3 py-2 shrink-0">
 <div className="flex items-center gap-1.5 overflow-x-auto">
 <span className="text-[10px] text-[var(--text-disabled)] shrink-0">{t("copilot.branches_sidebar")}:</span>
 <button
 onClick={() => setActiveBranchId("main")}
 className={cn(
"shrink-0 rounded-full px-2 py-0.5 text-[10px] font-medium transition-colors",
 activeBranchId ==="main"
 ?"bg-[var(--muhide-orange)] text-white"
 :"bg-[var(--bg-tertiary)] text-[var(--text-secondary)] hover:bg-[var(--bg-tertiary)]"
 )}
 >
 {t("copilot.branch_original")}
 </button>
 {branches.map((b, i) => (
 <button
 key={b.id}
 onClick={() => setActiveBranchId(b.id)}
 className={cn(
"shrink-0 rounded-full px-2 py-0.5 text-[10px] font-medium transition-colors",
 activeBranchId === b.id
 ?"bg-purple-600 text-white"
 :"bg-[var(--chart-purple-bg)] text-[var(--chart-purple)] hover:bg-[var(--chart-purple-bg)] dark:bg-[var(--bg-primary)]/30 dark:text-[var(--chart-purple)]"
 )}
 >
 <GitBranch className="inline h-2.5 w-2.5 me-0.5" />
 {b.label}
 </button>
 ))}
 </div>
 </div>
 )}

 <div className="border-t p-3 shrink-0">
 <div className="flex gap-2">
 <input
 value={input}
 onChange={(e) => setInput(e.target.value)}
 onKeyDown={(e) => e.key ==="Enter" && !e.shiftKey && handleSend()}
 placeholder={t("copilot.placeholder")}
 className="flex-1 rounded-lg border border-[var(--border-hover)] bg-[var(--bg-secondary)] px-3 py-2.5 text-sm outline-none focus:border-[var(--muhide-orange)] focus:ring-1 focus:ring-[var(--muhide-orange)]"
 />
 <button
 onClick={handleSend}
 disabled={!input.trim() || loading}
                className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-[var(--muhide-orange)] text-white hover:brightness-90 disabled:opacity-50"
 >
 <Send className="h-4 w-4" />
 </button>
 </div>
 <p className="mt-2 text-center text-[10px] text-[var(--text-disabled)]">
 {t("copilot.hint")}
 </p>
 </div>
 </>
 )}
 </div>
 )
}

function FeedbackButtons({
 msg, onFeedback, onSubmit, feedbackTarget, setFeedbackTarget, t,
}: {
 msg: Message
 onFeedback: (id: string, rating:"positive" |"negative") => void
 onSubmit: (id: string, comment?: string) => void
 feedbackTarget: string | null
 setFeedbackTarget: (id: string | null) => void
 t: (key: string) => string
}) {
 const [comment, setComment] = useState("")
 const agg = msg.aggregateFeedback

 if (msg.feedback?.submitted) {
 return (
 <span className="text-[10px] text-success-600 dark:text-success-400">
 {t("copilot.feedback_thanks")}
 </span>
 )
 }

 if (feedbackTarget === msg.id && msg.feedback) {
 return (
 <div className="flex flex-col gap-1.5 w-full">
 <div className="flex items-center gap-1">
 <MessageSquare className="h-3 w-3 text-[var(--text-disabled)]" />
 <textarea
 value={comment}
 onChange={(e) => setComment(e.target.value)}
 placeholder={t("copilot.feedback_comment_placeholder")}
 className="flex-1 rounded border border-[var(--border-default)] px-2 py-1 text-[11px] outline-none focus:border-[var(--muhide-orange)] resize-none"
 rows={2}
 />
 </div>
 <div className="flex gap-1">
 <button
 onClick={() => onSubmit(msg.id, comment)}
                className="rounded bg-[var(--muhide-orange)] px-2 py-0.5 text-[10px] text-white hover:brightness-90"
 >
 {t("copilot.feedback_submit")}
 </button>
 <button
 onClick={() => setFeedbackTarget(null)}
 className="rounded px-2 py-0.5 text-[10px] text-[var(--text-muted)] hover:bg-[var(--bg-tertiary)] dark:hover:bg-[var(--bg-secondary)]"
 >
 Cancel
 </button>
 </div>
 </div>
 )
 }

 return (
 <div className="flex items-center gap-1">
 <button
 onClick={() => onFeedback(msg.id,"positive")}
 className={cn(
"rounded-md p-1 transition-colors",
 msg.feedback?.rating ==="positive"
 ?"bg-success-100 text-success-700 dark:bg-success-900/30 dark:text-success-400"
 :"text-[var(--text-disabled)] hover:text-success-600 hover:bg-success-50 dark:hover:bg-success-900/20"
 )}
 title={t("copilot.feedback_helpful")}
 aria-label={t("copilot.feedback_positive")}
 >
 <ThumbsUp className="h-3.5 w-3.5" />
 </button>
 <button
 onClick={() => onFeedback(msg.id,"negative")}
 className={cn(
"rounded-md p-1 transition-colors",
 msg.feedback?.rating ==="negative"
 ?"bg-danger-100 text-danger-700 dark:bg-danger-900/30 dark:text-danger-400"
 :"text-[var(--text-disabled)] hover:text-danger-600 hover:bg-danger-50 dark:hover:bg-danger-900/20"
 )}
 aria-label={t("copilot.feedback_negative")}
 >
 <ThumbsDown className="h-3.5 w-3.5" />
 </button>
 {agg && agg.total > 0 && (
 <span className="text-[10px] text-[var(--text-disabled)] ms-1">
 {Math.round((agg.positive / agg.total) * 100)}% helpful
 </span>
 )}
 </div>
 )
}
