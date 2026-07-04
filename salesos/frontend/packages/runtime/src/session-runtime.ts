export interface SessionUser {
  id: string
  email: string
  name: string
  avatar?: string
  role: string
  permissions: string[]
  tenantId: string
  preferences: Record<string, unknown>
}

export interface Session {
  user: SessionUser | null
  token: string | null
  expiresAt: number | null
  authenticated: boolean
}

type SessionListener = (session: Session) => void

export class SessionRuntime {
  private session: Session = {
    user: null,
    token: null,
    expiresAt: null,
    authenticated: false,
  }
  private listeners = new Set<SessionListener>()
  private storageKey = 'salesos_session'

  constructor(storageKey?: string) {
    if (storageKey) this.storageKey = storageKey
    this.load()
  }

  private load() {
    if (typeof window === 'undefined') return
    try {
      const raw = localStorage.getItem(this.storageKey)
      if (raw) {
        const parsed = JSON.parse(raw)
        if (parsed.expiresAt && Date.now() < parsed.expiresAt) {
          this.session = parsed
        } else {
          localStorage.removeItem(this.storageKey)
        }
      }
    } catch {
      localStorage.removeItem(this.storageKey)
    }
  }

  private persist() {
    if (typeof window === 'undefined') return
    try {
      localStorage.setItem(this.storageKey, JSON.stringify(this.session))
    } catch {}
  }

  private notify() {
    this.listeners.forEach((fn) => fn(this.session))
  }

  getSession(): Session {
    return { ...this.session }
  }

  getUser(): SessionUser | null {
    return this.session.user
  }

  isAuthenticated(): boolean {
    return this.session.authenticated && this.session.expiresAt !== null && Date.now() < this.session.expiresAt
  }

  hasPermission(permission: string): boolean {
    return this.session.user?.permissions.includes(permission) ?? false
  }

  hasAnyPermission(permissions: string[]): boolean {
    return permissions.some((p) => this.hasPermission(p))
  }

  hasAllPermissions(permissions: string[]): boolean {
    return permissions.every((p) => this.hasPermission(p))
  }

  async login(user: SessionUser, token: string, expiresInMs: number): Promise<void> {
    this.session = {
      user,
      token,
      expiresAt: Date.now() + expiresInMs,
      authenticated: true,
    }
    this.persist()
    this.notify()
  }

  async refreshToken(token: string, expiresInMs: number): Promise<void> {
    if (this.session) {
      this.session.token = token
      this.session.expiresAt = Date.now() + expiresInMs
      this.persist()
      this.notify()
    }
  }

  async logout(): Promise<void> {
    this.session = { user: null, token: null, expiresAt: null, authenticated: false }
    if (typeof window !== 'undefined') {
      try {
        localStorage.removeItem(this.storageKey)
      } catch {}
    }
    this.notify()
  }

  updatePreferences(prefs: Record<string, unknown>): void {
    if (this.session.user) {
      this.session.user.preferences = { ...this.session.user.preferences, ...prefs }
      this.persist()
      this.notify()
    }
  }

  subscribe(listener: SessionListener): () => void {
    this.listeners.add(listener)
    return () => this.listeners.delete(listener)
  }
}
