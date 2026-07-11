import type { PluginContext } from './types'

export interface ApiClientConfig {
  baseUrl: string
  apiKey: string
  maxRetries?: number
  retryDelayMs?: number
  rateLimitPerSecond?: number
  timeoutMs?: number
}

export class ApiClient {
  private config: ApiClientConfig
  private requestCount: number = 0
  private windowStart: number = Date.now()

  constructor(config: ApiClientConfig) {
    this.config = {
      maxRetries: 3,
      retryDelayMs: 500,
      rateLimitPerSecond: 50,
      timeoutMs: 10000,
      ...config,
    }
  }

  static fromContext(ctx: PluginContext): ApiClient {
    return new ApiClient({
      baseUrl: ctx.apiBaseUrl,
      apiKey: ctx.apiKey,
    })
  }

  async get<T = unknown>(endpoint: string, params?: Record<string, unknown>): Promise<T> {
    const url = new URL(`${this.config.baseUrl}${endpoint}`)
    if (params) {
      for (const [key, value] of Object.entries(params)) {
        url.searchParams.set(key, String(value))
      }
    }
    return this.request<T>('GET', url.toString())
  }

  async post<T = unknown>(endpoint: string, data?: Record<string, unknown>): Promise<T> {
    return this.request<T>('POST', `${this.config.baseUrl}${endpoint}`, data)
  }

  async put<T = unknown>(endpoint: string, id: string, data?: Record<string, unknown>): Promise<T> {
    return this.request<T>('PUT', `${this.config.baseUrl}${endpoint}/${id}`, data)
  }

  async patch<T = unknown>(endpoint: string, id: string, data?: Record<string, unknown>): Promise<T> {
    return this.request<T>('PATCH', `${this.config.baseUrl}${endpoint}/${id}`, data)
  }

  async delete<T = unknown>(endpoint: string, id?: string): Promise<T> {
    const url = id ? `${this.config.baseUrl}${endpoint}/${id}` : `${this.config.baseUrl}${endpoint}`
    return this.request<T>('DELETE', url)
  }

  private async request<T>(
    method: string,
    url: string,
    body?: Record<string, unknown>,
    retries: number = 0,
  ): Promise<T> {
    await this.enforceRateLimit()

    const controller = new AbortController()
    const timeoutId = setTimeout(() => controller.abort(), this.config.timeoutMs)

    try {
      const headers: Record<string, string> = {
        'Authorization': `Bearer ${this.config.apiKey}`,
        'Content-Type': 'application/json',
        'X-Plugin-API-Version': '1',
      }

      const response = await fetch(url, {
        method,
        headers,
        body: body ? JSON.stringify(body) : undefined,
        signal: controller.signal,
      })

      if (!response.ok) {
        if (response.status === 429 && retries < (this.config.maxRetries ?? 3)) {
          const retryAfter = response.headers.get('Retry-After')
          const delayMs = retryAfter ? parseInt(retryAfter, 10) * 1000 : this.config.retryDelayMs!
          await this.sleep(delayMs)
          return this.request<T>(method, url, body, retries + 1)
        }

        if (response.status >= 500 && retries < (this.config.maxRetries ?? 3)) {
          await this.sleep(this.config.retryDelayMs! * Math.pow(2, retries))
          return this.request<T>(method, url, body, retries + 1)
        }

        const errorBody = await response.text().catch(() => '')
        throw new ApiError(response.status, response.statusText, errorBody)
      }

      return await response.json()
    } catch (err) {
      if (err instanceof ApiError) throw err
      if (retries < (this.config.maxRetries ?? 3)) {
        await this.sleep(this.config.retryDelayMs! * Math.pow(2, retries))
        return this.request<T>(method, url, body, retries + 1)
      }
      throw new ApiError(
        0,
        'NETWORK_ERROR',
        err instanceof Error ? err.message : 'Unknown network error',
      )
    } finally {
      clearTimeout(timeoutId)
    }
  }

  private async enforceRateLimit(): Promise<void> {
    const now = Date.now()
    if (now - this.windowStart > 1000) {
      this.requestCount = 0
      this.windowStart = now
    }

    if (this.requestCount >= (this.config.rateLimitPerSecond ?? 50)) {
      const waitMs = 1000 - (now - this.windowStart)
      if (waitMs > 0) {
        await this.sleep(waitMs)
      }
      this.requestCount = 0
      this.windowStart = Date.now()
    }

    this.requestCount++
  }

  private sleep(ms: number): Promise<void> {
    return new Promise((resolve) => setTimeout(resolve, ms))
  }
}

export class ApiError extends Error {
  constructor(
    public statusCode: number,
    public statusText: string,
    public body: string,
  ) {
    super(`API Error ${statusCode} ${statusText}: ${body.slice(0, 200)}`)
    this.name = 'ApiError'
  }

  isRateLimited(): boolean {
    return this.statusCode === 429
  }

  isUnauthorized(): boolean {
    return this.statusCode === 401
  }

  isForbidden(): boolean {
    return this.statusCode === 403
  }

  isNotFound(): boolean {
    return this.statusCode === 404
  }

  isServerError(): boolean {
    return this.statusCode >= 500
  }
}
