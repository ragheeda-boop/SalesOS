export {
  PluginRunner,
  createPluginRunner,
} from './hooks'
export type { PluginHooks } from './hooks'

export {
  ApiClient,
  ApiError,
} from './api-client'
export type { ApiClientConfig } from './api-client'

import type {
  PluginManifest,
  PluginDefinition,
  PluginValidationResult,
} from './types'

export type {
  PluginAuthor,
  PluginCapability,
  PluginContext,
  PluginAPI,
  PluginEvent,
  PluginError,
  PluginConfigChange,
  PluginResourceLimits,
  WebhookDeclaration,
} from './types'

export { type PluginDefinition, type PluginManifest, type PluginValidationResult }

export function validateManifest(manifest: PluginManifest): PluginValidationResult {
  const errors: string[] = []
  const warnings: string[] = []

  if (!manifest.id || manifest.id.trim().length === 0) {
    errors.push('manifest.id is required')
  }
  if (!manifest.plugin?.name || manifest.plugin.name.trim().length === 0) {
    errors.push('manifest.plugin.name is required')
  }
  if (!manifest.plugin?.version) {
    errors.push('manifest.plugin.version is required')
  }
  if (!manifest.entryPoint) {
    errors.push('manifest.entryPoint is required')
  }
  if (!manifest.plugin?.author?.name) {
    warnings.push('manifest.plugin.author.name is recommended')
  }
  if (!manifest.plugin?.description) {
    warnings.push('manifest.plugin.description is recommended')
  }
  if (manifest.plugin?.capabilities?.length === 0) {
    warnings.push('plugin declares no capabilities — it will not provide any extension')
  }

  return { valid: errors.length === 0, errors, warnings }
}

export function buildManifest(
  id: string,
  definition: import('./types').PluginDefinition,
  entryPoint: string,
): import('./types').PluginManifest {
  const now = new Date().toISOString()
  return {
    id,
    plugin: definition,
    entryPoint,
    hooks: [],
    widgets: [],
    workflows: [],
    dataSources: [],
    webhooks: [],
    resourceLimits: {
      maxCallsPerSecond: definition.resourceLimits?.maxCallsPerSecond ?? 100,
      maxMemoryMb: definition.resourceLimits?.maxMemoryMb ?? 50,
      maxTimeoutMs: definition.resourceLimits?.maxTimeoutMs ?? 5000,
      maxStorageKb: definition.resourceLimits?.maxStorageKb ?? 1024,
    },
    createdAt: now,
    updatedAt: now,
  }
}
