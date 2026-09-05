import type { LucideIcon } from "lucide-react";
import {
  Activity,
  BarChart3,
  Building2,
  Calendar,
  CheckSquare,
  ContactRound,
  Database,
  FileSignature,
  FileText,
  HeartHandshake,
  GitMerge,
  Home,
  Receipt,
  Settings,
  ShieldCheck,
  Shield,
  Target,
  Upload,
  Users,
  Zap,
} from "lucide-react";

export type V3NavItem = {
  href: string;
  label: string;
  icon: LucideIcon;
  keywords?: string[];
};

/** L2 domain nav — routes stay under /v3/* only. */
export const V3_DOMAIN_NAV: V3NavItem[] = [
  { href: "/v3", label: "Home", icon: Home, keywords: ["home", "workspace"] },
  {
    href: "/v3/companies",
    label: "Companies",
    icon: Building2,
    keywords: ["companies", "accounts", "orgs"],
  },
  {
    href: "/v3/crm",
    label: "CRM",
    icon: Target,
    keywords: ["crm", "pipeline", "deals", "leads"],
  },
  {
    href: "/v3/contacts",
    label: "Contacts",
    icon: ContactRound,
    keywords: ["contacts", "customers", "decision makers"],
  },
  {
    href: "/v3/people",
    label: "People",
    icon: Users,
    keywords: ["people", "employees", "owners"],
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
    href: "/v3/proposals",
    label: "Proposals",
    icon: FileText,
    keywords: ["proposals", "offers", "deals"],
  },
  {
    href: "/v3/quotes",
    label: "Quotes",
    icon: Receipt,
    keywords: ["quotes", "pricing", "line items", "offers"],
  },
  {
    href: "/v3/contracts",
    label: "Contracts",
    icon: FileSignature,
    keywords: ["contracts", "agreements", "sign", "legal"],
  },
  {
    href: "/v3/reviews",
    label: "Reviews",
    icon: ShieldCheck,
    keywords: ["reviews", "audit"],
  },
  {
    href: "/v3/approvals",
    label: "Approvals",
    icon: CheckSquare,
    keywords: ["approvals", "decisions", "review", "hitl"],
  },
  {
    href: "/v3/analytics",
    label: "Analytics",
    icon: BarChart3,
    keywords: ["analytics", "reports", "metrics"],
  },
  {
    href: "/v3/sales-dashboard",
    label: "Sales Dashboard",
    icon: Zap,
    keywords: ["sales", "dashboard", "actions", "signals", "daily", "priorities"],
  },
  {
    href: "/v3/my-day",
    label: "My Day",
    icon: Calendar,
    keywords: ["my day", "work queue", "today", "follow-ups", "outcomes"],
  },
  {
    href: "/v3/effectiveness",
    label: "Effectiveness",
    icon: BarChart3,
    keywords: ["effectiveness", "cohorts", "lift", "funnel", "conversion", "pipeline"],
  },
  {
    href: "/v3/cs",
    label: "CS",
    icon: HeartHandshake,
    keywords: ["cs", "customer success", "health"],
  },
  {
    href: "/v3/admin",
    label: "Admin",
    icon: Shield,
    keywords: ["admin", "flags", "governance"],
  },
  {
    href: "/v3/settings",
    label: "Settings",
    icon: Settings,
    keywords: ["settings", "preferences"],
  },
  {
    href: "/v3/data",
    label: "Data",
    icon: Database,
    keywords: ["master data", "companies", "people", "imports", "er", "quality"],
  },
  { href: "/v3/data/companies", label: "MD Companies", icon: Building2, keywords: ["master data", "companies", "global"] },
  { href: "/v3/data/people", label: "MD People", icon: Users, keywords: ["master data", "people", "contacts"] },
  { href: "/v3/data/imports", label: "Imports", icon: Upload, keywords: ["imports", "source files", "ingestion"] },
  { href: "/v3/data/er", label: "Entity Resolution", icon: GitMerge, keywords: ["er", "matching", "merge", "conflicts"] },
];

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
