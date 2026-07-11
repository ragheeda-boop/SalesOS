import type { PluginContext, PluginEvent, PluginError, PluginConfigChange } from './types'

export interface PluginHooks {
  onActivate?: (ctx: PluginContext) => void | Promise<void>
  onDeactivate?: (ctx: PluginContext) => void | Promise<void>
  onConfigChange?: (ctx: PluginContext, change: PluginConfigChange) => void | Promise<void>
  onEvent?: (ctx: PluginContext, event: PluginEvent) => void | Promise<void>
  onError?: (ctx: PluginContext, error: PluginError) => void | Promise<void>
  onInstall?: (ctx: PluginContext) => void | Promise<void>
  onUninstall?: (ctx: PluginContext) => void | Promise<void>
  onHealthCheck?: (ctx: PluginContext) => Promise<{ healthy: boolean; details?: string }>
}

export function createPluginRunner(hooks: PluginHooks, ctx: PluginContext): PluginRunner {
  return new PluginRunner(hooks, ctx)
}

export class PluginRunner {
  private hooks: PluginHooks
  private ctx: PluginContext
  private active: boolean = false

  constructor(hooks: PluginHooks, ctx: PluginContext) {
    this.hooks = hooks
    this.ctx = ctx
  }

  async activate(): Promise<void> {
    if (this.active) return
    this.active = true
    await this.safeRun('onActivate', this.hooks.onActivate?.(this.ctx))
  }

  async deactivate(): Promise<void> {
    if (!this.active) return
    this.active = false
    await this.safeRun('onDeactivate', this.hooks.onDeactivate?.(this.ctx))
  }

  async handleConfigChange(change: PluginConfigChange): Promise<void> {
    await this.safeRun('onConfigChange', this.hooks.onConfigChange?.(this.ctx, change))
  }

  async handleEvent(event: PluginEvent): Promise<void> {
    await this.safeRun('onEvent', this.hooks.onEvent?.(this.ctx, event))
  }

  async handleError(error: PluginError): Promise<void> {
    await this.safeRun('onError', this.hooks.onError?.(this.ctx, error))
  }

  async healthCheck(): Promise<{ healthy: boolean; details?: string }> {
    if (!this.hooks.onHealthCheck) return { healthy: true }
    try {
      return await this.hooks.onHealthCheck(this.ctx)
    } catch {
      return { healthy: false, details: 'Health check threw an exception' }
    }
  }

  isActive(): boolean {
    return this.active
  }

  private async safeRun(name: string, promise: void | Promise<void>): Promise<void> {
    if (!promise) return
    try {
      await promise
    } catch (err) {
      const error: PluginError = {
        code: 'HOOK_FAILED',
        message: `Plugin hook "${name}" failed: ${err instanceof Error ? err.message : String(err)}`,
        details: { hook: name, error: String(err) },
        recoverable: true,
      }
      await this.hooks.onError?.(this.ctx, error)
    }
  }
}
