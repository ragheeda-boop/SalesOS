import {
  LayoutDashboard,
  Building2,
  Users,
  UserCheck,
  DollarSign,
  ListChecks,
  TrendingUp,
  BarChart3,
  CalendarClock,
  Search,
  Brain,
  Video,
  GitGraph,
  Radio,
  HeartHandshake,
  Activity,
  Target,
  Radar,
  UserRoundSearch,
  Layers,
  Globe2,
  PenLine,
  BadgeCheck,
  Copy,
  Mail,
  Crosshair,
  FormInput,
  Gauge,
  KeyRound,
  Workflow,
  Bell,
  Palette,
  MapPin,
  Cpu,
  BookText,
  Scale,
  BrainCircuit,
  Store,
  Plug,
  Shield,
  Settings,
  type LucideIcon,
} from "lucide-react";

export interface NavItem {
  href: string;
  key: string;
  icon: LucideIcon;
}

export interface NavGroup {
  key: string;
  items: NavItem[];
}

export interface Workspace {
  id: string;
  key: string;
  icon: LucideIcon;
  groups: NavGroup[];
}

export const workspaces: Workspace[] = [
  {
    id: "sales",
    key: "workspace.sales",
    icon: DollarSign,
    groups: [
      {
        key: "workspace.group.core",
        items: [
          { href: "/dashboard", key: "nav.dashboard", icon: LayoutDashboard },
          { href: "/companies", key: "nav.companies", icon: Building2 },
          { href: "/employees", key: "nav.employees", icon: UserCheck },
          { href: "/employees/me", key: "nav.profile", icon: UserCheck },
          { href: "/contacts", key: "nav.contacts", icon: Users },
          { href: "/opportunities", key: "nav.opportunities", icon: DollarSign },
        ],
      },
      {
        key: "workspace.group.pipeline",
        items: [
          { href: "/revenue", key: "nav.revenue", icon: TrendingUp },
          { href: "/pipeline", key: "nav.pipeline", icon: BarChart3 },
          { href: "/forecast", key: "nav.forecast", icon: CalendarClock },
        ],
      },
      {
        key: "workspace.group.activity",
        items: [
          { href: "/activities", key: "nav.activities", icon: ListChecks },
          { href: "/meetings", key: "nav.meetings", icon: Video },
          { href: "/customer-success", key: "nav.customer_success", icon: HeartHandshake },
        ],
      },
    ],
  },
  {
    id: "executive",
    key: "workspace.executive",
    icon: Brain,
    groups: [
      {
        key: "workspace.group.decision",
        items: [
          { href: "/decisions", key: "nav.decisions", icon: Brain },
          { href: "/analytics", key: "nav.analytics", icon: BarChart3 },
          { href: "/graph", key: "nav.graph", icon: GitGraph },
        ],
      },
    ],
  },
  {
    id: "intelligence",
    key: "workspace.intelligence",
    icon: Search,
    groups: [
      {
        key: "workspace.group.discover",
        items: [
          { href: "/search", key: "nav.search", icon: Search },
          { href: "/signals", key: "nav.signals", icon: Radio },
          { href: "/monitoring", key: "nav.monitoring", icon: Activity },
          { href: "/rules", key: "nav.rules", icon: Shield },
        ],
      },
    ],
  },
  {
    id: "gtm",
    key: "workspace.gtm",
    icon: Crosshair,
    groups: [
      {
        key: "workspace.group.gtm",
        items: [
          { href: "/gtm", key: "nav.gtm_hub", icon: Crosshair },
          { href: "/gtm/icp", key: "nav.icp_profiles", icon: UserRoundSearch },
          { href: "/gtm/market-sizing", key: "nav.market_sizing", icon: Target },
          { href: "/gtm/lead-discovery", key: "nav.lead_discovery", icon: Radar },
          { href: "/gtm/enrichment", key: "nav.enrichment", icon: Layers },
          { href: "/gtm/website-intelligence", key: "nav.website_intelligence", icon: Globe2 },
          { href: "/gtm/outreach", key: "nav.outreach", icon: PenLine },
          { href: "/gtm/verification", key: "nav.verification", icon: BadgeCheck },
          { href: "/gtm/lookalikes", key: "nav.lookalikes", icon: Copy },
          { href: "/gtm/sequences", key: "nav.sequences", icon: Mail },
        ],
      },
    ],
  },
  {
    id: "studio",
    key: "workspace.studio",
    icon: Palette,
    groups: [
      {
        key: "workspace.group.customize",
        items: [
          { href: "/studio/custom-fields", key: "nav.custom_fields", icon: FormInput },
          { href: "/studio/scoring", key: "nav.scoring_rules", icon: Gauge },
          { href: "/studio/permissions", key: "nav.permissions_studio", icon: KeyRound },
          { href: "/studio/workflows", key: "nav.workflow_studio", icon: Workflow },
          { href: "/studio/notifications", key: "nav.notification_rules", icon: Bell },
          { href: "/studio/branding", key: "nav.branding_studio", icon: Palette },
          { href: "/studio/territories", key: "nav.territories_studio", icon: MapPin },
        ],
      },
      {
        key: "workspace.group.ai",
        items: [
          { href: "/studio/ai-model-tiers", key: "nav.ai_model_tiers", icon: Cpu },
          { href: "/studio/prompt-library", key: "nav.prompt_library", icon: BookText },
          { href: "/studio/ai-policies", key: "nav.ai_policies", icon: Scale },
          { href: "/studio/ai-memory", key: "nav.ai_memory", icon: BrainCircuit },
        ],
      },
    ],
  },
  {
    id: "admin",
    key: "workspace.admin",
    icon: Settings,
    groups: [
      {
        key: "workspace.group.system",
        items: [
          { href: "/settings", key: "nav.settings", icon: Settings },
          { href: "/admin", key: "nav.admin", icon: Shield },
          { href: "/integrations", key: "nav.integrations", icon: Plug },
          { href: "/marketplace/listings", key: "nav.marketplace_listings", icon: Store },
        ],
      },
    ],
  },
];

export function getWorkspaceByPath(pathname: string): Workspace {
  for (const ws of workspaces) {
    for (const group of ws.groups) {
      for (const item of group.items) {
        if (pathname.startsWith(item.href)) return ws;
      }
    }
  }
  return workspaces[0];
}

export function getAllNavItems(): NavItem[] {
  return workspaces.flatMap((ws) => ws.groups.flatMap((g) => g.items));
}
