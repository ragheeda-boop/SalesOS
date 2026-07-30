"use client"

import { useState, useEffect, useMemo, useCallback } from"react"
import { useQuery, useMutation, useQueryClient } from"@tanstack/react-query"
import {
 Search,
 Puzzle,
 Plug,
 BarChart3,
 Zap,
 Bot,
 Download,
 Trash2,
 Star,
 Settings,
 X,
 ExternalLink,
 CheckCircle2,
 AlertTriangle,
} from"lucide-react"
import {
 Button,
 Input,
 Badge,
 Card,
 CardContent,
 Modal,
 ModalContent,
 ModalHeader,
 ModalBody,
 ModalFooter,
 Spinner,
 EmptyState,
 Switch,
 Tooltip,
 Tabs,
 TabsList,
 Tab,
 TabsPanel,
} from"@salesos/ui"
import api from"@/lib/api"
import { useTenant } from"@/lib/hooks/useTenant"
import { useRouter } from"next/navigation"
import Link from"next/link"

interface PluginManifest {
 id: string
 name: string
 version: string
 description: string
 author: string
 permissions: string[]
 hooks: string[]
 config_schema?: Record<string, unknown>
 enabled: boolean
 installed: boolean
 installed_at?: string
 category?: string
 icon?: string
 rating?: number
 install_count?: number
 homepage?: string
}

interface PluginConfig {
 [key: string]: unknown
}

const CATEGORIES = [
 { id:"all", label:"All Plugins", icon: Puzzle },
 { id:"integration", label:"Integrations", icon: Plug },
 { id:"analytics", label:"Analytics", icon: BarChart3 },
 { id:"automation", label:"Automation", icon: Zap },
 { id:"ai", label:"AI & ML", icon: Bot },
] as const

type CategoryId = (typeof CATEGORIES)[number]["id"]

const CATEGORY_MAP: Record<string, string> = {
 slack:"integration",
 salesforce:"integration",
 zapier:"automation",
 tableau:"analytics",
 gpt:"ai",
 claude:"ai",
 email_sync:"integration",
 calendar_sync:"integration",
 reporting:"analytics",
 workflow:"automation",
}

function getCategory(plugin: PluginManifest): string {
 if (plugin.category) return plugin.category
 for (const [key, cat] of Object.entries(CATEGORY_MAP)) {
 if (plugin.id.toLowerCase().includes(key) || plugin.name.toLowerCase().includes(key)) {
 return cat
 }
 }
 return"integration"
}

const CATEGORY_ICONS: Record<string, typeof Plug> = {
 integration: Plug,
 analytics: BarChart3,
 automation: Zap,
 ai: Bot,
}

const BUILTIN_PLUGINS: PluginManifest[] = [
 {
 id:"slack-integration",
 name:"Slack Integration",
 version:"1.0.0",
 description:"Send notifications to Slack channels, sync messages, and receive alerts from SalesOS.",
 author:"SalesOS",
 permissions: ["notifications.write","channels.read"],
 hooks: ["notification.send","message.receive"],
  enabled: true,
  installed: false,
  category:"integration",
  rating: 4.8,
  install_count: 1240,
  config_schema: {
  type:"object",
  properties: {
  webhook_url: { type:"string", title:"Webhook URL", description:"Slack incoming webhook URL" },
  channel: { type:"string", title:"Default Channel", description:"Default Slack channel for notifications" },
  bot_token: { type:"string", title:"Bot Token", description:"Slack bot OAuth token", format:"password" },
  },
  required: ["webhook_url","channel"],
  },
  },
  {
  id:"salesforce-connector",
  name:"Salesforce Connector",
  version:"1.2.0",
  description:"Bi-directional sync with Salesforce CRM. Import leads, contacts, and opportunities.",
  author:"SalesOS",
  permissions: ["crm.read","crm.write","contacts.read","contacts.write"],
  hooks: ["company.sync","contact.sync","opportunity.sync"],
  enabled: true,
  installed: false,
 category:"integration",
 rating: 4.6,
 install_count: 890,
 config_schema: {
 type:"object",
 properties: {
 instance_url: { type:"string", title:"Instance URL", description:"Salesforce instance URL" },
 client_id: { type:"string", title:"Client ID", description:"Connected App Client ID" },
 client_secret: { type:"string", title:"Client Secret", description:"Connected App Client Secret", format:"password" },
 sync_interval: { type:"number", title:"Sync Interval (min)", description:"How often to sync data", default: 30 },
 },
 required: ["instance_url","client_id","client_secret"],
 },
 },
 {
 id:"zapier-automation",
 name:"Zapier Automation",
 version:"1.0.0",
 description:"Connect SalesOS to 5,000+ apps via Zapier. Trigger workflows on CRM events.",
 author:"SalesOS",
 permissions: ["workflows.execute","events.read"],
 hooks: ["opportunity.created","contact.updated","task.completed"],
 enabled: false,
 installed: false,
 category:"automation",
 rating: 4.5,
 install_count: 2100,
 },
 {
 id:"gpt-assistant",
 name:"GPT Assistant",
 version:"2.0.0",
 description:"AI-powered assistant for email drafts, meeting summaries, and deal insights.",
 author:"SalesOS AI",
 permissions: ["ai.generate","emails.read","meetings.read"],
 hooks: ["email.compose","meeting.summary","deal.analysis"],
  enabled: true,
  installed: false,
 category:"ai",
 rating: 4.9,
 install_count: 3200,
 config_schema: {
 type:"object",
 properties: {
 model: { type:"string", title:"AI Model", description:"Which GPT model to use", default:"gpt-4", enum: ["gpt-4","gpt-4-turbo","gpt-3.5-turbo"] },
 max_tokens: { type:"number", title:"Max Tokens", description:"Maximum tokens per request", default: 2048 },
 temperature: { type:"number", title:"Temperature", description:"Response creativity (0-1)", default: 0.7 },
 },
 },
 },
 {
 id:"tableau-analytics",
 name:"Tableau Analytics",
 version:"1.1.0",
 description:"Export SalesOS data to Tableau for advanced visualization and reporting.",
 author:"SalesOS",
 permissions: ["data.export","analytics.read"],
 hooks: ["report.export","dashboard.sync"],
 enabled: false,
 installed: false,
 category:"analytics",
 rating: 4.3,
 install_count: 560,
 },
 {
 id:"email-sync",
 name:"Email Sync",
 version:"1.0.0",
 description:"Sync emails from Outlook/Gmail to company timelines and contact records.",
 author:"SalesOS",
 permissions: ["emails.read","emails.sync"],
 hooks: ["email.received","email.sent"],
  enabled: true,
  installed: false,
 category:"integration",
 rating: 4.7,
 install_count: 1800,
 },
 {
 id:"claude-ai",
 name:"Claude AI",
 version:"1.0.0",
 description:"Anthropic's Claude for document analysis, contract review, and long-context reasoning.",
 author:"SalesOS AI",
 permissions: ["ai.generate","documents.read"],
 hooks: ["document.analysis","contract.review"],
 enabled: false,
 installed: false,
 category:"ai",
 rating: 4.8,
 install_count: 950,
 },
 {
 id:"workflow-automation",
 name:"Workflow Engine",
 version:"1.0.0",
 description:"Create custom automated workflows with triggers, conditions, and actions.",
 author:"SalesOS",
 permissions: ["workflows.manage","workflows.execute"],
 hooks: ["workflow.trigger"],
  enabled: true,
  installed: false,
 category:"automation",
 rating: 4.4,
 install_count: 1100,
 },
]

export default function MarketplacePage() {
 const { tenantId } = useTenant()
 const queryClient = useQueryClient()
 const router = useRouter()

 const [searchQuery, setSearchQuery] = useState("")
 const [activeCategory, setActiveCategory] = useState<CategoryId>("all")
 const [selectedPlugin, setSelectedPlugin] = useState<PluginManifest | null>(null)
 const [viewMode, setViewMode] = useState<"grid" |"list">("grid")

 const { data: remotePlugins, isLoading: remoteLoading } = useQuery({
 queryKey: ["marketplace","plugins"],
 queryFn: async () => {
 try {
 const res = await api.get("/api/v1/plugins", {
 headers: {"X-Tenant-Id": tenantId },
 })
 return (res.data || []) as PluginManifest[]
 } catch {
 return [] as PluginManifest[]
 }
 },
 })

 const plugins = useMemo(() => {
 const remote = remotePlugins || []
 const remoteIds = new Set(remote.map((p) => p.id))
 const builtinOnly = BUILTIN_PLUGINS.filter((b) => !remoteIds.has(b.id))
 return [...remote, ...builtinOnly]
 }, [remotePlugins])

 const filteredPlugins = useMemo(() => {
 return plugins.filter((p) => {
 const matchesSearch =
 !searchQuery ||
 p.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
 p.description.toLowerCase().includes(searchQuery.toLowerCase()) ||
 p.author.toLowerCase().includes(searchQuery.toLowerCase())
 const matchesCategory =
 activeCategory ==="all" || getCategory(p) === activeCategory
 return matchesSearch && matchesCategory
 })
 }, [plugins, searchQuery, activeCategory])

 const installedCount = plugins.filter((p) => p.installed).length

 const categoryCounts = useMemo(() => {
 const counts: Record<string, number> = { all: plugins.length }
 plugins.forEach((p) => {
 const cat = getCategory(p)
 counts[cat] = (counts[cat] || 0) + 1
 })
 return counts
 }, [plugins])

 const installMutation = useMutation({
 mutationFn: async (plugin: PluginManifest) => {
 await api.post(
"/api/v1/plugins/install",
 {
 plugin_id: plugin.id,
 name: plugin.name,
 version: plugin.version,
 description: plugin.description,
 author: plugin.author,
 permissions: plugin.permissions,
 hooks: plugin.hooks,
 },
 { headers: {"X-Tenant-Id": tenantId } }
 )
 },
 onSuccess: () => {
 queryClient.invalidateQueries({ queryKey: ["marketplace","plugins"] })
 setSelectedPlugin(null)
 },
 })

 const uninstallMutation = useMutation({
 mutationFn: async (pluginId: string) => {
 await api.delete(`/api/v1/plugins/${pluginId}`, {
 headers: {"X-Tenant-Id": tenantId },
 })
 },
 onSuccess: () => {
 queryClient.invalidateQueries({ queryKey: ["marketplace","plugins"] })
 setSelectedPlugin(null)
 },
 })

 const enableMutation = useMutation({
 mutationFn: async (pluginId: string) => {
 await api.post(`/api/v1/plugins/${pluginId}/enable`, null, {
 headers: {"X-Tenant-Id": tenantId },
 })
 },
 onSuccess: () => queryClient.invalidateQueries({ queryKey: ["marketplace","plugins"] }),
 })

 const disableMutation = useMutation({
 mutationFn: async (pluginId: string) => {
 await api.post(`/api/v1/plugins/${pluginId}/disable`, null, {
 headers: {"X-Tenant-Id": tenantId },
 })
 },
 onSuccess: () => queryClient.invalidateQueries({ queryKey: ["marketplace","plugins"] }),
 })

 const handleInstall = useCallback(
 (plugin: PluginManifest) => installMutation.mutate(plugin),
 [installMutation]
 )

 const handleUninstall = useCallback(
 (pluginId: string) => uninstallMutation.mutate(pluginId),
 [uninstallMutation]
 )

 const handleToggleEnabled = useCallback(
 (plugin: PluginManifest) => {
 if (!plugin.installed) return
 if (plugin.enabled) {
 disableMutation.mutate(plugin.id)
 } else {
 enableMutation.mutate(plugin.id)
 }
 },
 [enableMutation, disableMutation]
 )

 const handleConfigure = useCallback(
 (plugin: PluginManifest) => {
 router.push(`/marketplace/${plugin.id}/config`)
 },
 [router]
 )

 function renderStars(rating: number) {
 const full = Math.floor(rating)
 const hasHalf = rating - full >= 0.3
 return (
 <div className="flex items-center gap-0.5">
 {Array.from({ length: 5 }).map((_, i) => (
 <Star
 key={i}
 className={`h-3 w-3 ${
 i < full
 ?"fill-amber-400 text-[var(--status-warning-text)]"
 : i === full && hasHalf
 ?"fill-amber-400/50 text-[var(--status-warning-text)]"
 :"text-[var(--text-disabled)]"
 }`}
 />
 ))}
 </div>
 )
 }

 if (remoteLoading) {
 return (
 <div className="flex min-h-[400px] items-center justify-center">
 <Spinner className="h-8 w-8 text-[var(--muhide-orange)]" />
 </div>
 )
 }

 return (
 <div className="space-y-6">
 {/* Header */}
 <div className="flex items-center justify-between">
 <div>
 <h1 className="text-2xl font-bold text-[var(--text-primary)]">Marketplace</h1>
 <p className="mt-1 text-sm text-[var(--text-secondary)]">
 Browse and install plugins to extend SalesOS
 </p>
 </div>
 <div className="flex items-center gap-2">
 <Badge variant="outline">{installedCount} installed</Badge>
 <div className="flex rounded-lg border border-[var(--border-default)]">
 <button
 onClick={() => setViewMode("grid")}
 className={`px-2.5 py-1.5 text-xs font-medium transition-colors ${
 viewMode ==="grid"
 ?"bg-[var(--muhide-orange)]/10 text-[var(--muhide-orange)]"
 :"text-[var(--text-muted)] hover:text-[var(--text-secondary)]"
 }`}
 >
 Grid
 </button>
 <button
 onClick={() => setViewMode("list")}
 className={`px-2.5 py-1.5 text-xs font-medium transition-colors ${
 viewMode ==="list"
 ?"bg-[var(--muhide-orange)]/10 text-[var(--muhide-orange)]"
 :"text-[var(--text-muted)] hover:text-[var(--text-secondary)]"
 }`}
 >
 List
 </button>
 </div>
 </div>
 </div>

 {/* Search + Filters */}
 <div className="flex flex-col gap-4 sm:flex-row sm:items-center">
 <div className="relative flex-1">
 <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-[var(--text-muted)]" />
 <Input
 placeholder="Search plugins..."
 value={searchQuery}
 onChange={(e) => setSearchQuery(e.target.value)}
 leftIcon={<Search className="h-4 w-4" />}
 className="pl-10"
 />
 </div>
 </div>

 {/* Category Tabs */}
 <Tabs value={activeCategory} onValueChange={(v) => setActiveCategory(v as CategoryId)}>
 <TabsList className="flex-wrap">
 {CATEGORIES.map((cat) => {
 const Icon = cat.icon
 return (
 <Tab key={cat.id} value={cat.id} className="flex items-center gap-1.5">
 <Icon className="h-3.5 w-3.5" />
 {cat.label}
 <span className="ml-1 text-[10px] text-[var(--text-muted)]">
 {categoryCounts[cat.id] || 0}
 </span>
 </Tab>
 )
 })}
 </TabsList>
 </Tabs>

 {/* Plugin Grid / List */}
 {filteredPlugins.length === 0 ? (
 <EmptyState
 icon={<Puzzle className="h-10 w-10" />}
 title="No plugins found"
 description="Try adjusting your search or category filter."
 />
 ) : viewMode ==="grid" ? (
 <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
 {filteredPlugins.map((plugin) => {
 const cat = getCategory(plugin)
 const CatIcon = CATEGORY_ICONS[cat] || Puzzle
 return (
 <Card
 key={plugin.id}
 className="group cursor-pointer transition-all hover:border-[var(--muhide-orange)] hover:shadow-muhide-2"
 onClick={() => setSelectedPlugin(plugin)}
 >
 <CardContent className="p-5">
 <div className="flex items-start gap-3">
 <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-[var(--muhide-orange)]/10">
 <CatIcon className="h-5 w-5 text-[var(--muhide-orange)]" />
 </div>
 <div className="min-w-0 flex-1">
 <div className="flex items-center gap-2">
 <h3 className="truncate text-sm font-semibold text-[var(--text-primary)]">
 {plugin.name}
 </h3>
 {plugin.installed && (
 <Badge variant="success" className="shrink-0">
 Installed
 </Badge>
 )}
 </div>
 <p className="mt-0.5 text-xs text-[var(--text-muted)]">
 v{plugin.version} by {plugin.author}
 </p>
 </div>
 </div>
 <p className="mt-3 line-clamp-2 text-xs text-[var(--text-secondary)]">
 {plugin.description}
 </p>
 <div className="mt-3 flex items-center justify-between">
 <div className="flex items-center gap-2">
 {plugin.rating && renderStars(plugin.rating)}
 {plugin.rating && (
 <span className="text-[10px] text-[var(--text-muted)]">
 {plugin.rating}
 </span>
 )}
 </div>
 {plugin.installed ? (
 <div className="flex items-center gap-1.5" onClick={(e) => e.stopPropagation()}>
 <Switch
 checked={plugin.enabled}
 size="sm"
 onChange={() => handleToggleEnabled(plugin)}
 />
 <Button
 size="sm"
 variant="ghost"
 onClick={() => handleConfigure(plugin)}
 >
 <Settings className="h-3.5 w-3.5" />
 </Button>
 </div>
 ) : (
 <Button
 size="sm"
 onClick={(e) => {
 e.stopPropagation()
 handleInstall(plugin)
 }}
 disabled={installMutation.isPending}
 >
 <Download className="h-3.5 w-3.5" />
 Install
 </Button>
 )}
 </div>
 </CardContent>
 </Card>
 )
 })}
 </div>
 ) : (
 <div className="space-y-2">
 {filteredPlugins.map((plugin) => {
 const cat = getCategory(plugin)
 const CatIcon = CATEGORY_ICONS[cat] || Puzzle
 return (
 <Card
 key={plugin.id}
 className="cursor-pointer transition-all hover:border-[var(--muhide-orange)]"
 onClick={() => setSelectedPlugin(plugin)}
 >
 <div className="flex items-center gap-4 p-4">
 <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-[var(--muhide-orange)]/10">
 <CatIcon className="h-5 w-5 text-[var(--muhide-orange)]" />
 </div>
 <div className="min-w-0 flex-1">
 <div className="flex items-center gap-2">
 <h3 className="text-sm font-semibold text-[var(--text-primary)]">
 {plugin.name}
 </h3>
 {plugin.installed && (
 <Badge variant="success">Installed</Badge>
 )}
 <span className="text-xs text-[var(--text-muted)]">
 v{plugin.version}
 </span>
 <span className="text-xs text-[var(--text-muted)]">
 by {plugin.author}
 </span>
 </div>
 <p className="mt-0.5 line-clamp-1 text-xs text-[var(--text-secondary)]">
 {plugin.description}
 </p>
 </div>
 <div className="flex items-center gap-3">
 {plugin.rating && (
 <div className="flex items-center gap-1">
 <Star className="h-3 w-3 fill-amber-400 text-[var(--status-warning-text)]" />
 <span className="text-xs text-[var(--text-muted)]">{plugin.rating}</span>
 </div>
 )}
 <div onClick={(e) => e.stopPropagation()}>
 {plugin.installed ? (
 <div className="flex items-center gap-2">
 <Switch
 checked={plugin.enabled}
 size="sm"
 onChange={() => handleToggleEnabled(plugin)}
 />
 <Button
 size="sm"
 variant="ghost"
 onClick={() => handleConfigure(plugin)}
 >
 <Settings className="h-3.5 w-3.5" />
 </Button>
 </div>
 ) : (
 <Button
 size="sm"
 onClick={() => handleInstall(plugin)}
 disabled={installMutation.isPending}
 >
 <Download className="h-3.5 w-3.5" />
 Install
 </Button>
 )}
 </div>
 </div>
 </div>
 </Card>
 )
 })}
 </div>
 )}

 {/* Plugin Detail Modal */}
 <Modal open={!!selectedPlugin} onOpenChange={(open) => !open && setSelectedPlugin(null)}>
 <ModalContent className="max-w-xl">
 {selectedPlugin && (
 <>
 <ModalHeader>
 <div className="flex items-center gap-3">
 <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-[var(--muhide-orange)]/10">
 {(() => {
 const cat = getCategory(selectedPlugin)
 const CatIcon = CATEGORY_ICONS[cat] || Puzzle
 return <CatIcon className="h-5 w-5 text-[var(--muhide-orange)]" />
 })()}
 </div>
 <div>
 <h2 className="text-lg font-semibold text-[var(--text-primary)]">
 {selectedPlugin.name}
 </h2>
 <p className="text-xs text-[var(--text-muted)]">
 v{selectedPlugin.version} by {selectedPlugin.author}
 </p>
 </div>
 </div>
 </ModalHeader>
 <ModalBody>
 <div className="space-y-4">
 <p className="text-sm text-[var(--text-secondary)]">{selectedPlugin.description}</p>

 <div className="flex items-center gap-4">
 {selectedPlugin.rating && (
 <div className="flex items-center gap-1.5">
 {renderStars(selectedPlugin.rating)}
 <span className="text-xs font-medium text-[var(--text-primary)]">
 {selectedPlugin.rating}
 </span>
 </div>
 )}
 {selectedPlugin.install_count && (
 <span className="text-xs text-[var(--text-muted)]">
 {selectedPlugin.install_count.toLocaleString()} installs
 </span>
 )}
 </div>

 <div>
 <h4 className="mb-2 text-xs font-semibold uppercase tracking-wider text-[var(--text-muted)]">
 Permissions Required
 </h4>
 <div className="flex flex-wrap gap-1.5">
 {selectedPlugin.permissions.map((perm) => (
 <Badge key={perm} variant="outline" className="text-[10px]">
 {perm}
 </Badge>
 ))}
 </div>
 </div>

 {selectedPlugin.hooks.length > 0 && (
 <div>
 <h4 className="mb-2 text-xs font-semibold uppercase tracking-wider text-[var(--text-muted)]">
 Hook Points
 </h4>
 <div className="flex flex-wrap gap-1.5">
 {selectedPlugin.hooks.map((hook) => (
 <Badge key={hook} variant="default" className="text-[10px]">
 {hook}
 </Badge>
 ))}
 </div>
 </div>
 )}

 {selectedPlugin.config_schema && selectedPlugin.installed && (
 <div className="rounded-lg bg-[var(--bg-secondary)] p-3">
 <div className="flex items-center gap-2 text-xs text-[var(--text-secondary)]">
 <Settings className="h-3.5 w-3.5" />
 This plugin has configurable settings
 </div>
 </div>
 )}

 {selectedPlugin.homepage && (
 <a
 href={selectedPlugin.homepage}
 target="_blank"
 rel="noopener noreferrer"
 className="inline-flex items-center gap-1 text-xs text-[var(--muhide-orange)] hover:underline"
 onClick={(e) => e.stopPropagation()}
 >
 <ExternalLink className="h-3 w-3" />
 Documentation
 </a>
 )}
 </div>
 </ModalBody>
 <ModalFooter>
 {selectedPlugin.installed ? (
 <div className="flex items-center gap-2">
 <Switch
 checked={selectedPlugin.enabled}
 label={selectedPlugin.enabled ?"Enabled" :"Disabled"}
 onChange={() => handleToggleEnabled(selectedPlugin)}
 />
 {selectedPlugin.config_schema && (
 <Button
 variant="outline"
 onClick={() => {
 setSelectedPlugin(null)
 handleConfigure(selectedPlugin)
 }}
 >
 <Settings className="h-4 w-4" />
 Configure
 </Button>
 )}
 <Button
 variant="danger"
 onClick={() => handleUninstall(selectedPlugin.id)}
 disabled={uninstallMutation.isPending}
 >
 <Trash2 className="h-4 w-4" />
 Uninstall
 </Button>
 </div>
 ) : (
 <Button
 onClick={() => handleInstall(selectedPlugin)}
 disabled={installMutation.isPending}
 >
 <Download className="h-4 w-4" />
 {installMutation.isPending ?"Installing..." :"Install Plugin"}
 </Button>
 )}
 </ModalFooter>
 </>
 )}
 </ModalContent>
 </Modal>
 </div>
 )
}
