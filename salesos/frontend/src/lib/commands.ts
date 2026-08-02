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
    handler: () => router.push("/dashboard"),
  });

  registerCommand({
    id: "go.companies",
    label: "الشركات",
    description: "الانتقال إلى قائمة الشركات",
    category: "تنقل",
    shortcut: "G C",
    handler: () => router.push("/companies"),
  });

  registerCommand({
    id: "go.search",
    label: "البحث العام",
    description: "فتح البحث العام",
    category: "تنقل",
    shortcut: "G S",
    handler: () => router.push("/search"),
  });

  registerCommand({
    id: "go.integrations",
    label: "التكاملات",
    description: "Integrations Studio (Hub HTTP)",
    category: "تنقل",
    shortcut: "G I",
    handler: () => router.push("/integrations"),
  });

  registerCommand({
    id: "go.integrations.connect",
    label: "Integrations · Connect",
    description: "Studio Connect step (tip ?step=connect)",
    category: "تنقل",
    handler: () => router.push("/integrations?step=connect"),
  });

  registerCommand({
    id: "go.integrations.test",
    label: "Integrations · Test",
    description: "Studio Test step (tip ?step=test)",
    category: "تنقل",
    handler: () => router.push("/integrations?step=test"),
  });

  registerCommand({
    id: "go.integrations.map",
    label: "Integrations · Map",
    description: "Studio Map step (tip ?step=map)",
    category: "تنقل",
    handler: () => router.push("/integrations?step=map"),
  });

  registerCommand({
    id: "go.integrations.conflict",
    label: "Integrations · Conflict",
    description: "Studio Conflict step (tip ?step=conflict)",
    category: "تنقل",
    handler: () => router.push("/integrations?step=conflict"),
  });

  registerCommand({
    id: "go.integrations.schedule",
    label: "Integrations · Schedule",
    description: "Studio Schedule step (tip ?step=schedule)",
    category: "تنقل",
    handler: () => router.push("/integrations?step=schedule"),
  });

  registerCommand({
    id: "go.integrations.monitor",
    label: "Integrations · Monitor",
    description: "Studio Monitor step (tip ?step=monitor)",
    category: "تنقل",
    handler: () => router.push("/integrations?step=monitor"),
  });

  registerCommand({
    id: "go.integrations.disconnect",
    label: "Integrations · Disconnect",
    description: "Studio Disconnect step (tip ?step=disconnect)",
    category: "تنقل",
    handler: () => router.push("/integrations?step=disconnect"),
  });

  registerCommand({
    id: "go.settings",
    label: "الإعدادات",
    description: "الانتقال إلى الإعدادات",
    category: "تنقل",
    shortcut: "G ,",
    handler: () => router.push("/settings"),
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
