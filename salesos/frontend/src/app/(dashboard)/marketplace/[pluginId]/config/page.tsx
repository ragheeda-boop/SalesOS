"use client"

import { useState, useEffect, useCallback } from"react"
import { useQuery, useMutation, useQueryClient } from"@tanstack/react-query"
import {
 ArrowLeft,
 Save,
 TestTube,
 CheckCircle2,
 AlertTriangle,
 Settings,
 Shield,
 Power,
 PowerOff,
 RefreshCw,
} from"lucide-react"
import {
 Button,
 Input,
 Badge,
 Card,
 CardContent,
 CardHeader,
 Switch,
 Spinner,
 Select,
 Textarea,
} from"@salesos/ui"
import api from"@/lib/api"
import { useTenant } from"@/lib/hooks/useTenant"
import { useRouter, useParams } from"next/navigation"
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
 config?: Record<string, unknown>
}

interface SchemaProperty {
 type: string
 title?: string
 description?: string
 default?: unknown
 format?: string
 enum?: string[]
 minimum?: number
 maximum?: number
}

function renderFormField(
 key: string,
 prop: SchemaProperty,
 value: unknown,
 onChange: (key: string, value: unknown) => void,
 required: boolean
) {
 const label = prop.title || key
 const isPassword = prop.format ==="password"
 const isNumber = prop.type ==="number"
 const isEnum = prop.enum && prop.enum.length > 0

 if (isEnum) {
 return (
 <Select
 key={key}
 options={(prop.enum || []).map((v) => ({ label: v, value: v }))}
 placeholder={`Select ${label}`}
 value={String(value ?? prop.default ??"")}
 onChange={(v) => onChange(key, v)}
 />
 )
 }

 if (isNumber) {
 return (
 <Input
 key={key}
 type="number"
 label={label}
 value={String(value ?? prop.default ??"")}
 onChange={(e) => onChange(key, Number(e.target.value))}
 min={prop.minimum}
 max={prop.maximum}
 />
 )
 }

 if (prop.type ==="string" && (prop.description ||"").length > 80) {
 return (
 <Textarea
 key={key}
 label={label}
 value={String(value ?? prop.default ??"")}
 onChange={(e) => onChange(key, e.target.value)}
 placeholder={prop.description}
 />
 )
 }

 return (
 <Input
 key={key}
 type={isPassword ?"password" :"text"}
 label={label}
 value={String(value ?? prop.default ??"")}
 onChange={(e) => onChange(key, e.target.value)}
 placeholder={prop.description}
 />
 )
}

export default function PluginConfigPage() {
 const { pluginId } = useParams<{ pluginId: string }>()
 const { tenantId } = useTenant()
 const router = useRouter()
 const queryClient = useQueryClient()

 const [configValues, setConfigValues] = useState<Record<string, unknown>>({})
 const [testStatus, setTestStatus] = useState<"idle" |"testing" |"success" |"error">("idle")
 const [testMessage, setTestMessage] = useState("")

 const { data: plugin, isLoading } = useQuery({
 queryKey: ["marketplace","plugin", pluginId],
 queryFn: async () => {
 try {
 const res = await api.get(`/api/v1/plugins/${pluginId}`, {
 headers: {"X-Tenant-Id": tenantId },
 })
 return res.data as PluginManifest
 } catch {
 return null
 }
 },
 })

 useEffect(() => {
 if (plugin?.config) {
 setConfigValues(plugin.config)
 } else if (plugin?.config_schema) {
 const schema = plugin.config_schema as { properties?: Record<string, SchemaProperty> }
 if (schema.properties) {
 const defaults: Record<string, unknown> = {}
 Object.entries(schema.properties).forEach(([key, prop]) => {
 if (prop.default !== undefined) defaults[key] = prop.default
 })
 setConfigValues(defaults)
 }
 }
 }, [plugin])

 const saveMutation = useMutation({
 mutationFn: async (config: Record<string, unknown>) => {
 await api.put(
 `/api/v1/plugins/${pluginId}/config`,
 { config },
 { headers: {"X-Tenant-Id": tenantId } }
 )
 },
 onSuccess: () => {
 queryClient.invalidateQueries({ queryKey: ["marketplace","plugins"] })
 },
 })

 const enableMutation = useMutation({
 mutationFn: async (enabled: boolean) => {
 const endpoint = enabled
 ? `/api/v1/plugins/${pluginId}/enable`
 : `/api/v1/plugins/${pluginId}/disable`
 await api.post(endpoint, null, {
 headers: {"X-Tenant-Id": tenantId },
 })
 },
 onSuccess: () => {
 queryClient.invalidateQueries({ queryKey: ["marketplace","plugins"] })
 queryClient.invalidateQueries({ queryKey: ["marketplace","plugin", pluginId] })
 },
 })

 const testConnection = useCallback(async () => {
 setTestStatus("testing")
 setTestMessage("")
 try {
 const res = await api.post(
 `/api/v1/plugins/${pluginId}/test`,
 { config: configValues },
 { headers: {"X-Tenant-Id": tenantId } }
 )
 setTestStatus("success")
 setTestMessage(res.data?.message ||"Connection successful")
 } catch (err: unknown) {
 setTestStatus("error")
 const axiosErr = err as { response?: { data?: { detail?: string } } }
 setTestMessage(axiosErr.response?.data?.detail ||"Connection test failed")
 }
 }, [pluginId, configValues, tenantId])

 const handleConfigChange = useCallback((key: string, value: unknown) => {
 setConfigValues((prev) => ({ ...prev, [key]: value }))
 setTestStatus("idle")
 }, [])

 if (isLoading) {
 return (
 <div className="flex min-h-[400px] items-center justify-center">
 <Spinner className="h-8 w-8 text-[var(--muhide-orange)]" />
 </div>
 )
 }

 if (!plugin) {
 return (
 <div className="space-y-6 p-6">
 <Link
 href="/marketplace"
 className="inline-flex items-center gap-1.5 text-sm text-[var(--text-muted)] hover:text-[var(--text-primary)]"
 >
 <ArrowLeft className="h-4 w-4" />
 Back to Marketplace
 </Link>
 <Card className="p-8 text-center">
 <AlertTriangle className="mx-auto h-8 w-8 text-[var(--status-warning-text)]" />
 <h2 className="mt-3 text-lg font-semibold text-[var(--text-primary)]">Plugin not found</h2>
 <p className="mt-1 text-sm text-[var(--text-secondary)]">
 The plugin could not be loaded. It may not be installed.
 </p>
 <Button className="mt-4" onClick={() => router.push("/marketplace")}>
 Back to Marketplace
 </Button>
 </Card>
 </div>
 )
 }

 const schema = plugin.config_schema as { properties?: Record<string, SchemaProperty>; required?: string[] } | undefined
 const properties = schema?.properties || {}
 const requiredFields = new Set(schema?.required || [])
 const isIntegration = plugin.hooks.some(
 (h) => h.includes("sync") || h.includes("connect") || h.includes("send")
 )
 const hasConfigSchema = Object.keys(properties).length > 0

 return (
 <div className="mx-auto max-w-3xl space-y-6">
 {/* Back link */}
 <Link
 href="/marketplace"
 className="inline-flex items-center gap-1.5 text-sm text-[var(--text-muted)] hover:text-[var(--text-primary)]"
 >
 <ArrowLeft className="h-4 w-4" />
 Back to Marketplace
 </Link>

 {/* Plugin Header */}
 <Card>
 <CardContent className="p-6">
 <div className="flex items-start justify-between">
 <div className="flex items-start gap-4">
 <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-[var(--muhide-orange)]/10">
 <Settings className="h-6 w-6 text-[var(--muhide-orange)]" />
 </div>
 <div>
 <h1 className="text-xl font-bold text-[var(--text-primary)]">{plugin.name}</h1>
 <p className="mt-0.5 text-sm text-[var(--text-secondary)]">
 v{plugin.version} by {plugin.author}
 </p>
 <p className="mt-1 text-sm text-[var(--text-muted)]">{plugin.description}</p>
 </div>
 </div>
 <div className="flex items-center gap-3">
 <div className="flex items-center gap-2">
 <span className="text-sm text-[var(--text-secondary)]">
 {plugin.enabled ?"Enabled" :"Disabled"}
 </span>
 <Switch
 checked={plugin.enabled}
 size="md"
 onChange={() => enableMutation.mutate(!plugin.enabled)}
 disabled={enableMutation.isPending}
 />
 </div>
 </div>
 </div>
 </CardContent>
 </Card>

 {/* Permissions */}
 {plugin.permissions.length > 0 && (
 <Card>
 <CardHeader>
 <div className="flex items-center gap-2">
 <Shield className="h-4 w-4 text-[var(--muhide-orange)]" />
 <h2 className="text-sm font-semibold text-[var(--text-primary)]">
 Required Permissions
 </h2>
 </div>
 </CardHeader>
 <CardContent>
 <div className="flex flex-wrap gap-1.5">
 {plugin.permissions.map((perm) => (
 <Badge key={perm} variant="outline" className="text-xs">
 {perm}
 </Badge>
 ))}
 </div>
 <p className="mt-2 text-xs text-[var(--text-muted)]">
 These permissions are required for the plugin to function correctly.
 </p>
 </CardContent>
 </Card>
 )}

 {/* Configuration Form */}
 {hasConfigSchema && (
 <Card>
 <CardHeader>
 <div className="flex items-center gap-2">
 <Settings className="h-4 w-4 text-[var(--muhide-orange)]" />
 <h2 className="text-sm font-semibold text-[var(--text-primary)]">Configuration</h2>
 </div>
 </CardHeader>
 <CardContent>
 <div className="space-y-4">
 {Object.entries(properties).map(([key, prop]) => (
 <div key={key}>
 {renderFormField(
 key,
 prop,
 configValues[key],
 handleConfigChange,
 requiredFields.has(key)
 )}
 {prop.description && (
 <p className="mt-1 text-[10px] text-[var(--text-muted)]">{prop.description}</p>
 )}
 </div>
 ))}
 </div>

 <div className="mt-6 flex items-center gap-3">
 <Button
 onClick={() => saveMutation.mutate(configValues)}
 disabled={saveMutation.isPending}
 >
 {saveMutation.isPending ? (
 <Spinner className="h-4 w-4" />
 ) : (
 <Save className="h-4 w-4" />
 )}
 Save Configuration
 </Button>

 {isIntegration && (
 <Button
 variant="outline"
 onClick={testConnection}
 disabled={testStatus ==="testing"}
 >
 {testStatus ==="testing" ? (
 <Spinner className="h-4 w-4" />
 ) : (
 <TestTube className="h-4 w-4" />
 )}
 Test Connection
 </Button>
 )}

 {testStatus !=="idle" && testStatus !=="testing" && (
 <div
 className={`flex items-center gap-2 rounded-lg px-3 py-1.5 text-xs ${
 testStatus ==="success"
 ?"bg-success-50 text-success-700 dark:bg-success-900/20 dark:text-success-400"
 :"bg-danger-50 text-danger-700 dark:bg-danger-900/20 dark:text-danger-400"
 }`}
 >
 {testStatus ==="success" ? (
 <CheckCircle2 className="h-3.5 w-3.5" />
 ) : (
 <AlertTriangle className="h-3.5 w-3.5" />
 )}
 {testMessage}
 </div>
 )}
 </div>

 {saveMutation.isSuccess && (
 <div className="mt-3 flex items-center gap-2 rounded-lg bg-success-50 px-3 py-2 text-xs text-success-700 dark:bg-success-900/20 dark:text-success-400">
 <CheckCircle2 className="h-3.5 w-3.5" />
 Configuration saved successfully
 </div>
 )}
 {saveMutation.isError && (
 <div className="mt-3 flex items-center gap-2 rounded-lg bg-danger-50 px-3 py-2 text-xs text-danger-700 dark:bg-danger-900/20 dark:text-danger-400">
 <AlertTriangle className="h-3.5 w-3.5" />
 Failed to save configuration
 </div>
 )}
 </CardContent>
 </Card>
 )}

 {/* Hook Points */}
 {plugin.hooks.length > 0 && (
 <Card>
 <CardHeader>
 <h2 className="text-sm font-semibold text-[var(--text-primary)]">Hook Points</h2>
 </CardHeader>
 <CardContent>
 <div className="space-y-2">
 {plugin.hooks.map((hook) => (
 <div
 key={hook}
 className="flex items-center justify-between rounded-lg border border-[var(--border-default)] px-3 py-2"
 >
 <span className="text-sm text-[var(--text-primary)]">{hook}</span>
 <Badge variant="success">Active</Badge>
 </div>
 ))}
 </div>
 </CardContent>
 </Card>
 )}
 </div>
 )
}
