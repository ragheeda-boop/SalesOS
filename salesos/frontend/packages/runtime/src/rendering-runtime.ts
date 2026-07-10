export interface RenderingOptions {
  renderMode?: 'server' | 'client' | 'hybrid'
  streamingEnabled?: boolean
  progressiveLoading?: boolean
  suspenseThreshold?: number
  componentCacheEnabled?: boolean
}

export interface RenderRequest {
  schemaId: string
  props: Record<string, unknown>
  context?: Record<string, unknown>
}

export interface RenderResult {
  component: string
  props: Record<string, unknown>
  children?: RenderResult[]
  loading?: boolean
  error?: string
  fallback?: RenderResult
}

type RenderingListener = (request: RenderRequest, result: RenderResult) => void

export class RenderingRuntime {
  private options: RenderingOptions
  private renderListeners = new Set<RenderingListener>()
  private componentRegistry = new Map<string, { priority: number; loader: () => Promise<unknown> }>()
  private componentCache = new Map<string, RenderResult>()

  constructor(options?: RenderingOptions) {
    this.options = {
      renderMode: 'hybrid',
      streamingEnabled: true,
      progressiveLoading: true,
      suspenseThreshold: 300,
      componentCacheEnabled: true,
      ...options,
    }
  }

  getOptions(): RenderingOptions {
    return { ...this.options }
  }

  setOptions(options: Partial<RenderingOptions>): void {
    this.options = { ...this.options, ...options }
  }

  registerComponent(name: string, priority: number, loader: () => Promise<unknown>): void {
    this.componentRegistry.set(name, { priority, loader })
  }

  getRegisteredComponents(): string[] {
    return Array.from(this.componentRegistry.keys())
  }

  async render(request: RenderRequest): Promise<RenderResult> {
    const cacheKey = `${request.schemaId}:${JSON.stringify(request.props)}`
    if (this.options.componentCacheEnabled) {
      const cached = this.componentCache.get(cacheKey)
      if (cached) return cached
    }
    const result: RenderResult = {
      component: request.schemaId,
      props: request.props,
    }
    this.renderListeners.forEach((fn) => fn(request, result))
    if (this.options.componentCacheEnabled) {
      this.componentCache.set(cacheKey, result)
      if (this.componentCache.size > 200) {
        const first = this.componentCache.keys().next().value
        if (first) this.componentCache.delete(first)
      }
    }
    return result
  }

  async preloadComponent(name: string): Promise<void> {
    const entry = this.componentRegistry.get(name)
    if (entry) {
      try {
        await entry.loader()
      } catch (e) {
        console.warn(`[RenderingRuntime] Failed to preload component "${name}":`, e)
      }
    }
  }

  preloadComponents(names: string[]): Promise<void>[] {
    return names.map((name) => this.preloadComponent(name))
  }

  shouldSuspend(componentName: string): boolean {
    return (this.options.progressiveLoading ?? false) && this.componentRegistry.has(componentName)
  }

  subscribe(listener: RenderingListener): () => void {
    this.renderListeners.add(listener)
    return () => this.renderListeners.delete(listener)
  }

  invalidateCache(schemaId?: string): void {
    if (schemaId) {
      for (const key of this.componentCache.keys()) {
        if (key.startsWith(schemaId)) this.componentCache.delete(key)
      }
    } else {
      this.componentCache.clear()
    }
  }

  destroy(): void {
    this.componentCache.clear()
    this.componentRegistry.clear()
    this.renderListeners.clear()
  }
}
