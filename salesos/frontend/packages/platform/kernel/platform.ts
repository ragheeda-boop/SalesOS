export interface PlatformConfig {
  permissions?: PermissionResolver
  featureFlags?: FeatureFlagResolver
  telemetry?: TelemetryProvider
  cache?: CacheProvider
}

export interface PermissionResolver {
  hasPermission(resource: string, action: string, context?: Record<string, unknown>): boolean
}

export interface FeatureFlagResolver {
  isEnabled(flag: { enabled: boolean; tier?: string }): boolean
}

export interface TelemetryProvider {
  recordMetric(name: string, value: number, tags?: Record<string, string>): void
  incrementCounter(name: string, tags?: Record<string, string>): void
  recordHistogram(name: string, value: number, tags?: Record<string, string>): void
}

export interface CacheProvider {
  get<T>(key: string): Promise<T | undefined>
  set<T>(key: string, value: T, ttlMs?: number): Promise<void>
  delete(key: string): Promise<void>
}

export class Platform {
  private _permissions: PermissionResolver
  private _featureFlags: FeatureFlagResolver
  private _telemetry: TelemetryProvider
  private _cache: CacheProvider

  constructor(config: PlatformConfig) {
    this._permissions = config.permissions ?? { hasPermission: () => true }
    this._featureFlags = config.featureFlags ?? { isEnabled: () => true }
    this._telemetry = config.telemetry ?? {
      recordMetric: () => {},
      incrementCounter: () => {},
      recordHistogram: () => {},
    }
    this._cache = config.cache ?? {
      get: async () => undefined,
      set: async () => {},
      delete: async () => {},
    }
  }

  get permissions(): PermissionResolver { return this._permissions }
  get featureFlags(): FeatureFlagResolver { return this._featureFlags }
  get telemetry(): TelemetryProvider { return this._telemetry }
  get cache(): CacheProvider { return this._cache }
}
