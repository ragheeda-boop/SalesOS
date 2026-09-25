import type { LucideIcon } from "lucide-react";
import {
  Activity,
  BookOpen,
  Brain,
  Building2,
  CheckSquare,
  ContactRound,
  FileSignature,
  FileText,
  Home,
  Receipt,
  Settings,
  ShieldCheck,
  Target,
  Crosshair,
  Sparkles,
} from "lucide-react";

export type V3NavItem = {
  href: string;
  label: string;
  icon: LucideIcon;
  keywords?: string[];
};

/**
 * Primary customer chrome — MVP golden path (~12).
 * Commercial create surfaces (L3/L8–L16) stay here. Pages not listed remain routed.
 */
export const V3_DOMAIN_NAV: V3NavItem[] = [
  { href: "/v3", label: "Home", icon: Home, keywords: ["home", "workspace"] },
  {
    href: "/v3/companies",
    label: "Companies",
    icon: Building2,
    keywords: ["companies", "accounts", "orgs"],
  },
  {
    href: "/v3/contacts",
    label: "Contacts",
    icon: ContactRound,
    keywords: ["contacts", "customers", "decision makers"],
  },
  {
    href: "/v3/crm",
    label: "CRM",
    icon: Target,
    keywords: ["crm", "pipeline", "deals", "leads"],
  },
  {
    href: "/v3/activities",
    label: "Activities",
    icon: Activity,
    keywords: ["activities", "timeline", "feed", "meetings"],
  },
  {
    href: "/v3/tasks",
    label: "Tasks",
    icon: CheckSquare,
    keywords: ["tasks", "todos", "follow-ups"],
  },
  {
    href: "/v3/quotes",
    label: "Quotes",
    icon: Receipt,
    keywords: ["quotes", "pricing", "line items", "offers"],
  },
  {
    href: "/v3/proposals",
    label: "Proposals",
    icon: FileText,
    keywords: ["proposals", "offers", "deals"],
  },
  {
    href: "/v3/reviews",
    label: "Reviews",
    icon: ShieldCheck,
    keywords: ["reviews", "audit"],
  },
  {
    href: "/v3/contracts",
    label: "Contracts",
    icon: FileSignature,
    keywords: ["contracts", "agreements", "sign", "legal"],
  },
  {
    href: "/v3/icp",
    label: "ICP",
    icon: Crosshair,
    keywords: ["icp", "ideal customer", "profile", "fit", "criteria"],
  },
  {
    href: "/v3/settings",
    label: "Settings",
    icon: Settings,
    keywords: ["settings", "preferences", "gmail", "integrations"],
  },
];

/**
 * Extra v3 CmdK destinations beyond primary chrome.
 * `/v3/shell` stays on disk (internal spec) — do not advertise it to customers.
 */
export const V3_CMD_EXTRA: V3NavItem[] = [
  {
    href: "/v3/admin/ai-prompts",
    label: "Prompt Library",
    icon: FileText,
    keywords: ["prompt", "template", "AI studio"],
  },
  {
    href: "/v3/admin/ai-policies",
    label: "AI Policies",
    icon: ShieldCheck,
    keywords: ["policy", "guardrails", "data class"],
  },
  {
    href: "/v3/admin/ai-memory",
    label: "AI Memory",
    icon: Brain,
    keywords: ["memory", "conversation", "AI studio"],
  },
  {
    href: "/v3/admin/ai-model-tiers",
    label: "AI Model Tiers",
    icon: Settings,
    keywords: ["model", "tier", "plan defaults"],
  },
  {
    href: "/v3/rag",
    label: "Knowledge workspace",
    icon: BookOpen,
    keywords: ["rag", "knowledge", "documents", "citations", "ask"],
  },
  {
    href: "/v3/recommendations",
    label: "Recommended actions",
    icon: Sparkles,
    keywords: ["recommendations", "next action", "deal health", "evidence"],
  },
  {
    href: "/v3/admin/ai-governance",
    label: "AI Governance Audit",
    icon: ShieldCheck,
    keywords: ["ai policy", "governance", "audit", "guardrails", "pii"],
  },
  {
    href: "/v3/evidence",
    label: "Evidence chain",
    icon: FileText,
    keywords: ["evidence", "sources", "provenance", "confidence", "insights"],
  },
];

export function isV3NavActive(pathname: string, href: string): boolean {
  if (href === "/v3") return pathname === "/v3" || pathname === "/v3/";
  return pathname === href || pathname.startsWith(`${href}/`);
}
