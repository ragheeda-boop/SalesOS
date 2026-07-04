export interface CollaborationSession {
  sessionId: string
  entityType: string
  entityId: string
  users: Collaborator[]
  cursors: Map<string, CursorPosition>
}

export interface Collaborator {
  userId: string
  name: string
  avatar?: string
  color: string
  online: boolean
  lastActive: number
}

export interface CursorPosition {
  userId: string
  x: number
  y: number
  element?: string
  updatedAt: number
}

type CollaborationListener = {
  onUserJoin?: (user: Collaborator) => void
  onUserLeave?: (userId: string) => void
  onCursorMove?: (cursor: CursorPosition) => void
  onPresenceChange?: (users: Collaborator[]) => void
}

const COLLABORATOR_COLORS = [
  '#3B82F6', '#EF4444', '#10B981', '#F59E0B', '#8B5CF6',
  '#EC4899', '#14B8A6', '#F97316', '#6366F1', '#84CC16',
]

export class CollaborationRuntime {
  private sessions = new Map<string, CollaborationSession>()
  private listeners = new Map<string, Set<CollaborationListener>>()
  private currentUserId: string | null = null
  private colorIndex = 0

  setCurrentUser(userId: string): void {
    this.currentUserId = userId
  }

  joinSession(entityType: string, entityId: string, user: { userId: string; name: string; avatar?: string }): CollaborationSession {
    const sessionKey = `${entityType}:${entityId}`
    let session = this.sessions.get(sessionKey)
    if (!session) {
      session = {
        sessionId: sessionKey,
        entityType,
        entityId,
        users: [],
        cursors: new Map(),
      }
      this.sessions.set(sessionKey, session)
    }
    if (!session.users.find((u) => u.userId === user.userId)) {
      const collaborator: Collaborator = {
        ...user,
        color: COLLABORATOR_COLORS[this.colorIndex++ % COLLABORATOR_COLORS.length],
        online: true,
        lastActive: Date.now(),
      }
      session.users.push(collaborator)
      this.notify(sessionKey, 'onUserJoin', collaborator)
      this.notify(sessionKey, 'onPresenceChange', session.users)
    }
    return session
  }

  leaveSession(entityType: string, entityId: string): void {
    const sessionKey = `${entityType}:${entityId}`
    const session = this.sessions.get(sessionKey)
    if (!session || !this.currentUserId) return
    session.users = session.users.filter((u) => u.userId !== this.currentUserId)
    session.cursors.delete(this.currentUserId)
    this.notify(sessionKey, 'onUserLeave', this.currentUserId)
    this.notify(sessionKey, 'onPresenceChange', session.users)
    if (session.users.length === 0) this.sessions.delete(sessionKey)
  }

  updateCursor(entityType: string, entityId: string, position: Partial<CursorPosition>): void {
    const sessionKey = `${entityType}:${entityId}`
    const session = this.sessions.get(sessionKey)
    if (!session || !this.currentUserId) return
    const existing = session.cursors.get(this.currentUserId) || {
      userId: this.currentUserId,
      x: 0,
      y: 0,
      updatedAt: Date.now(),
    }
    const updated: CursorPosition = { ...existing, ...position, updatedAt: Date.now() }
    session.cursors.set(this.currentUserId, updated)
    this.notify(sessionKey, 'onCursorMove', updated)
  }

  updatePresence(entityType: string, entityId: string): void {
    const sessionKey = `${entityType}:${entityId}`
    const session = this.sessions.get(sessionKey)
    if (!session || !this.currentUserId) return
    const user = session.users.find((u) => u.userId === this.currentUserId)
    if (user) {
      user.lastActive = Date.now()
      user.online = true
    }
  }

  setUserOffline(userId: string): void {
    for (const session of this.sessions.values()) {
      const user = session.users.find((u) => u.userId === userId)
      if (user) {
        user.online = false
        this.notify(session.sessionId, 'onPresenceChange', session.users)
      }
    }
  }

  getSession(entityType: string, entityId: string): CollaborationSession | undefined {
    return this.sessions.get(`${entityType}:${entityId}`)
  }

  subscribe(sessionKey: string, listener: CollaborationListener): () => void {
    if (!this.listeners.has(sessionKey)) {
      this.listeners.set(sessionKey, new Set())
    }
    this.listeners.get(sessionKey)!.add(listener)
    return () => this.listeners.get(sessionKey)?.delete(listener)
  }

  private notify(sessionKey: string, event: keyof CollaborationListener, data: any) {
    const listeners = this.listeners.get(sessionKey)
    if (listeners) {
      listeners.forEach((l) => {
        const handler = l[event]
        if (handler) handler(data)
      })
    }
  }

  getActiveSessions(): CollaborationSession[] {
    return Array.from(this.sessions.values())
  }

  destroy(): void {
    this.sessions.clear()
    this.listeners.clear()
  }
}
