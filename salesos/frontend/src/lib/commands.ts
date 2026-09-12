"use client";

import { registerCommand } from "@salesos/hooks";
import { useRouter } from "next/navigation";

export function registerBuiltinCommands(router: ReturnType<typeof useRouter>) {
  registerCommand({
    id: "go.dashboard",
    label: "لوحة المعلومات",
    description: "الانتقال إلى لوحة المعلومات",
    category: "تنقل",
    shortcut: "G D",
    handler: () => router.push("/v3"),
  });

  registerCommand({
    id: "go.companies",
    label: "الشركات",
    description: "الانتقال إلى قائمة الشركات",
    category: "تنقل",
    shortcut: "G C",
    handler: () => router.push("/v3/companies"),
  });

  // Search hub `/search` stays on disk (FREEZE — later embed in v3 topbar) — do not advertise.
  // Overlay toggle stays as action.search (salesos:toggle-search), not this hub.

  // Integrations Studio + Tenant Studio + Marketplace listings stay on disk (tip / MVP-out) — do not advertise.
  // Gmail OAuth stays on /v3/settings (go.settings), not this studio.
  registerCommand({
    id: "go.v3.quotes",
    label: "V3 · Quotes",
    description: "View and manage quotes",
    category: "تنقل",
    shortcut: "G Q",
    handler: () => router.push("/v3/quotes"),
  });

  registerCommand({
    id: "go.v3.contracts",
    label: "V3 · Contracts",
    description: "View and manage contracts",
    category: "تنقل",
    handler: () => router.push("/v3/contracts"),
  });

  // Approvals / Data / Review Queue stay on disk but are off primary MVP chrome — do not advertise.
  registerCommand({
    id: "go.settings",
    label: "الإعدادات",
    description: "الانتقال إلى الإعدادات",
    category: "تنقل",
    shortcut: "G ,",
    handler: () => router.push("/v3/settings"),
  });

  registerCommand({
    id: "go.admin",
    label: "الإدارة",
    description: "الانتقال إلى لوحة الإدارة",
    category: "تنقل",
    shortcut: "G A",
    handler: () => router.push("/admin"),
  });

  registerCommand({
    id: "action.copilot",
    label: "فتح المساعد الذكي",
    description: "تشغيل المساعد الذكي AI",
    category: "إجراءات",
    shortcut: "Ctrl+I",
    handler: () => {
      window.dispatchEvent(new CustomEvent("salesos:toggle-copilot"));
    },
  });

  registerCommand({
    id: "action.search",
    label: "فتح البحث",
    description: "فتح شريط البحث العام",
    category: "إجراءات",
    shortcut: "Ctrl+K",
    handler: () => {
      window.dispatchEvent(new CustomEvent("salesos:toggle-search"));
    },
  });

  registerCommand({
    id: "action.theme",
    label: "تبديل السمة",
    description: "التبديل بين الوضع الفاتح والداكن",
    category: "إجراءات",
    shortcut: "Ctrl+T",
    handler: () => {
      window.dispatchEvent(new CustomEvent("salesos:toggle-theme"));
    },
  });

  registerCommand({
    id: "action.help",
    label: "المساعدة",
    description: "عرض المساعدة والتعليمات",
    category: "إجراءات",
    shortcut: "?",
    handler: () => {
      window.dispatchEvent(new CustomEvent("salesos:toggle-help"));
    },
  });
}
