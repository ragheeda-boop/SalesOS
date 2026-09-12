import type { LucideIcon } from "lucide-react";
import {
  Activity,
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

/** Internal spec — still in v3 CmdK; not primary chrome. Page stays. */
export const V3_CMD_EXTRA: V3NavItem[] = [
  {
    href: "/v3/shell",
    label: "Shell spec",
    icon: Home,
    keywords: ["shell", "spec", "chrome"],
  },
];

export function isV3NavActive(pathname: string, href: string): boolean {
  if (href === "/v3") return pathname === "/v3" || pathname === "/v3/";
  return pathname === href || pathname.startsWith(`${href}/`);
}
