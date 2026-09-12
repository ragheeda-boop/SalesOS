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

  // Leftover-layout palette: jump to remaining MVP v3 destinations (do not
  // duplicate home/companies/settings — those already land in v3).
  registerCommand({
    id: "go.v3.contacts",
    label: "V3 · Contacts",
    description: "View and manage contacts",
    category: "تنقل",
    handler: () => router.push("/v3/contacts"),
  });

  registerCommand({
    id: "go.v3.crm",
    label: "V3 · CRM",
    description: "View deals and pipeline",
    category: "تنقل",
    handler: () => router.push("/v3/crm"),
  });

  registerCommand({
    id: "go.v3.activities",
    label: "V3 · Activities",
    description: "View the activities feed",
    category: "تنقل",
    handler: () => router.push("/v3/activities"),
  });

  registerCommand({
    id: "go.v3.tasks",
    label: "V3 · Tasks",
    description: "View and manage tasks",
    category: "تنقل",
    handler: () => router.push("/v3/tasks"),
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
    id: "go.v3.proposals",
    label: "V3 · Proposals",
    description: "View and manage proposals",
    category: "تنقل",
    handler: () => router.push("/v3/proposals"),
  });

  registerCommand({
    id: "go.v3.reviews",
    label: "V3 · Reviews",
    description: "View and manage reviews",
    category: "تنقل",
    handler: () => router.push("/v3/reviews"),
  });

  registerCommand({
    id: "go.v3.contracts",
    label: "V3 · Contracts",
    description: "View and manage contracts",
    category: "تنقل",
    handler: () => router.push("/v3/contracts"),
  });

  registerCommand({
    id: "go.v3.icp",
    label: "V3 · ICP",
    description: "View ICP profiles",
    category: "تنقل",
    handler: () => router.push("/v3/icp"),
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

  // AI copilot stays off (feature_ai_copilot default False) — do not advertise.
  // Do not flip the flag. Do not build copilot UI.

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

  // Help overlay stays unbuilt — leftover layout has no salesos:toggle-help listener.
  // Do not advertise. Leave action.search / action.theme (wired overlays).
}
