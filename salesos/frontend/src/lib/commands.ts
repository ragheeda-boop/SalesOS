"use client"

import { registerCommand } from "@salesos/hooks"
import { useRouter } from "next/navigation"

export function registerBuiltinCommands(router: ReturnType<typeof useRouter>) {
  registerCommand({
    id: "go.dashboard",
    label: "لوحة المعلومات",
    description: "الانتقال إلى لوحة المعلومات",
    category: "تنقل",
    shortcut: "G D",
    handler: () => router.push("/dashboard"),
  })

  registerCommand({
    id: "go.companies",
    label: "الشركات",
    description: "الانتقال إلى قائمة الشركات",
    category: "تنقل",
    shortcut: "G C",
    handler: () => router.push("/companies"),
  })

  registerCommand({
    id: "go.search",
    label: "البحث العام",
    description: "فتح البحث العام",
    category: "تنقل",
    shortcut: "G S",
    handler: () => router.push("/search"),
  })

  registerCommand({
    id: "go.settings",
    label: "الإعدادات",
    description: "الانتقال إلى الإعدادات",
    category: "تنقل",
    shortcut: "G ,",
    handler: () => router.push("/settings"),
  })

  registerCommand({
    id: "action.copilot",
    label: "فتح المساعد الذكي",
    description: "تشغيل المساعد الذكي AI",
    category: "إجراءات",
    shortcut: "Ctrl+I",
    handler: () => {
      window.dispatchEvent(new CustomEvent("salesos:toggle-copilot"))
    },
  })

  registerCommand({
    id: "action.search",
    label: "فتح البحث",
    description: "فتح شريط البحث العام",
    category: "إجراءات",
    shortcut: "Ctrl+K",
    handler: () => {
      window.dispatchEvent(new CustomEvent("salesos:toggle-search"))
    },
  })

  registerCommand({
    id: "action.theme",
    label: "تبديل السمة",
    description: "التبديل بين الوضع الفاتح والداكن",
    category: "إجراءات",
    shortcut: "Ctrl+T",
    handler: () => {
      window.dispatchEvent(new CustomEvent("salesos:toggle-theme"))
    },
  })

  registerCommand({
    id: "action.help",
    label: "المساعدة",
    description: "عرض المساعدة والتعليمات",
    category: "إجراءات",
    shortcut: "?",
    handler: () => {
      window.dispatchEvent(new CustomEvent("salesos:toggle-help"))
    },
  })
}
