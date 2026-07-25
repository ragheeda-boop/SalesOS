import type { LucideIcon } from 'lucide-react'
import {
 Activity,
 BarChart3,
 Building2,
 CheckSquare,
 ContactRound,
 HeartHandshake,
 Home,
 Settings,
 Shield,
 Target,
 Users,
} from 'lucide-react'

export type V3NavItem = {
 href: string
 label: string
 icon: LucideIcon
 keywords?: string[]
}

/** L2 domain nav — routes stay under /v3/* only. */
export const V3_DOMAIN_NAV: V3NavItem[] = [
 { href: '/v3', label: 'Home', icon: Home, keywords: ['home', 'workspace'] },
 {
 href: '/v3/companies',
 label: 'Companies',
 icon: Building2,
 keywords: ['companies', 'accounts', 'orgs'],
 },
 {
 href: '/v3/crm',
 label: 'CRM',
 icon: Target,
 keywords: ['crm', 'pipeline', 'deals', 'leads'],
 },
 {
 href: '/v3/contacts',
 label: 'Contacts',
 icon: ContactRound,
 keywords: ['contacts', 'customers', 'decision makers'],
 },
 {
 href: '/v3/people',
 label: 'People',
 icon: Users,
 keywords: ['people', 'employees', 'owners'],
 },
 {
 href: '/v3/activities',
 label: 'Activities',
 icon: Activity,
 keywords: ['activities', 'timeline', 'feed', 'meetings'],
 },
 {
 href: '/v3/tasks',
 label: 'Tasks',
 icon: CheckSquare,
 keywords: ['tasks', 'todos', 'follow-ups'],
 },
 {
 href: '/v3/analytics',
 label: 'Analytics',
 icon: BarChart3,
 keywords: ['analytics', 'reports', 'metrics'],
 },
 {
 href: '/v3/cs',
 label: 'CS',
 icon: HeartHandshake,
 keywords: ['cs', 'customer success', 'health'],
 },
 {
 href: '/v3/admin',
 label: 'Admin',
 icon: Shield,
 keywords: ['admin', 'flags', 'governance'],
 },
 {
 href: '/v3/settings',
 label: 'Settings',
 icon: Settings,
 keywords: ['settings', 'preferences'],
 },
]

export const V3_CMD_EXTRA: V3NavItem[] = [
 {
 href: '/v3/shell',
 label: 'Shell spec',
 icon: Home,
 keywords: ['shell', 'spec', 'chrome'],
 },
]

export function isV3NavActive(pathname: string, href: string): boolean {
 if (href === '/v3') return pathname === '/v3' || pathname === '/v3/'
 return pathname === href || pathname.startsWith(`${href}/`)
}
