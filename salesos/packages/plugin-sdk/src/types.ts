export type PluginCapability =
  | 'widget'
  | 'workflow'
  | 'data-source'
  | 'webhook'
  | 'dashboard-card'
  | 'search-provider'
  | 'notification-channel'

export interface PluginAuthor {
  name: string
  email?: string
  url?: string
}

export interface PluginResourceLimits {
  maxCallsPerSecond: number
  maxMemoryMb: number
  maxTimeoutMs: number
  maxStorageKb: number
}

export interface PluginDefinition {
  name: string
  version: string
  description: string
  author: PluginAuthor
  capabilities: PluginCapability[]
  permissions: string[]
  dependencies: string[]
  icon?: string
  tags?: string[]
  homepage?: string
  license?: string
  configSchema?: Record<string, unknown>
  resourceLimits?: Partial<PluginResourceLimits>
}

export interface PluginManifest {
  id: string
  plugin: PluginDefinition
  entryPoint: string
  hooks: string[]
  widgets: string[]
  workflows: string[]
  dataSources: string[]
  webhooks: WebhookDeclaration[]
  resourceLimits: PluginResourceLimits
  createdAt: string
  updatedAt: string
}

export interface WebhookDeclaration {
  name: string
  description: string
  events: string[]
  url: string
  method: 'GET' | 'POST' | 'PUT' | 'PATCH' | 'DELETE'
  secret?: boolean
}

export interface PluginContext {
  tenantId: string
  userId: string
  pluginId: string
  instanceId: string
  config: Record<string, unknown>
  apiBaseUrl: string
  apiKey: string
  metadata?: Record<string, unknown>
}

export interface PluginAPI {
  query: <T = unknown>(endpoint: string, params?: Record<string, unknown>) => Promise<T>
  create: <T = unknown>(endpoint: string, data: Record<string, unknown>) => Promise<T>
  update: <T = unknown>(endpoint: string, id: string, data: Record<string, unknown>) => Promise<T>
  delete: <T = unknown>(endpoint: string, id: string) => Promise<T>
  getConfig: <T = Record<string, unknown>>() => T
  updateConfig: (config: Record<string, unknown>) => Promise<void>
  getStorage: <T = unknown>(key: string) => Promise<T | null>
  setStorage: (key: string, value: unknown) => Promise<void>
  deleteStorage: (key: string) => Promise<void>
  publishEvent: (eventType: string, payload: Record<string, unknown>) => Promise<void>
  subscribeToEvent: (eventType: string, handler: (payload: Record<string, unknown>) => void) => () => void
  checkPermission: (permission: string) => Promise<boolean>
  log: (level: 'info' | 'warn' | 'error', message: string, data?: Record<string, unknown>) => void
  reportMetric: (name: string, value: number, tags?: Record<string, string | number | boolean>) => void
}

export interface PluginEvent {
  id: string
  type: string
  source: string
  payload: Record<string, unknown>
  tenantId: string
  timestamp: string
}

export interface PluginError {
  code: string
  message: string
  details?: Record<string, unknown>
  recoverable: boolean
}

export interface PluginConfigChange {
  previous: Record<string, unknown>
  current: Record<string, unknown>
  changedKeys: string[]
}

export interface PluginValidationResult {
  valid: boolean
  errors: string[]
  warnings: string[]
}
