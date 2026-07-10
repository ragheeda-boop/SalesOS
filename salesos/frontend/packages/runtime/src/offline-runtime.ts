export interface OfflineAction {
  id: string
  type: string
  payload: unknown
  entityType?: string
  entityId?: string
  timestamp: number
  retryCount: number
  maxRetries: number
}

export interface OfflineQueue {
  actions: OfflineAction[]
  lastSyncAt: number | null
  pendingCount: number
  failedCount: number
}

type OfflineStatus = 'online' | 'offline' | 'syncing'
type OfflineListener = (status: OfflineStatus) => void

export class OfflineRuntime {
  private online: boolean = typeof window !== 'undefined' ? navigator.onLine : true
  private queue: OfflineAction[] = []
  private statusListeners = new Set<OfflineListener>()
  private syncInProgress = false
  private storageKey = 'salesos_offline_queue'
  private maxRetries = 3
  private actionCounter = 0

  constructor() {
    if (typeof window !== 'undefined') {
      window.addEventListener('online', () => this.setOnline(true))
      window.addEventListener('offline', () => this.setOnline(false))
      this.loadQueue()
    }
  }

  private setOnline(value: boolean) {
    this.online = value
    this.notifyStatus()
    if (value && this.queue.length > 0) {
      this.sync()
    }
  }

  private notifyStatus() {
    const status = this.getStatus()
    this.statusListeners.forEach((fn) => fn(status))
  }

  private loadQueue() {
    try {
      const raw = localStorage.getItem(this.storageKey)
      if (raw) this.queue = JSON.parse(raw)
    } catch {
      this.queue = []
    }
  }

  private persistQueue() {
    try {
      localStorage.setItem(this.storageKey, JSON.stringify(this.queue))
    } catch (e) {
      console.warn('[OfflineRuntime] Failed to persist offline queue:', e)
    }
  }

  isOnline(): boolean {
    return this.online
  }

  getStatus(): OfflineStatus {
    if (this.syncInProgress) return 'syncing'
    return this.online ? 'online' : 'offline'
  }

  enqueue(action: Omit<OfflineAction, 'id' | 'timestamp' | 'retryCount' | 'maxRetries'>): OfflineAction {
    const entry: OfflineAction = {
      ...action,
      id: `offline_${++this.actionCounter}_${Date.now()}`,
      timestamp: Date.now(),
      retryCount: 0,
      maxRetries: this.maxRetries,
    }
    this.queue.push(entry)
    this.persistQueue()
    return entry
  }

  dequeue(actionId: string): void {
    this.queue = this.queue.filter((a) => a.id !== actionId)
    this.persistQueue()
  }

  markFailed(actionId: string): void {
    const action = this.queue.find((a) => a.id === actionId)
    if (action) {
      action.retryCount++
      if (action.retryCount >= action.maxRetries) {
        this.dequeue(actionId)
      }
      this.persistQueue()
    }
  }

  async sync(): Promise<void> {
    if (this.syncInProgress || this.queue.length === 0) return
    this.syncInProgress = true
    this.notifyStatus()
    const actions = [...this.queue]
    for (const action of actions) {
      if (action.retryCount >= action.maxRetries) {
        this.dequeue(action.id)
        continue
      }
      this.dequeue(action.id)
    }
    this.syncInProgress = false
    this.notifyStatus()
    if (this.online && this.queue.length > 0) {
      setTimeout(() => this.sync(), 1000)
    }
  }

  getQueue(): OfflineQueue {
    return {
      actions: [...this.queue],
      lastSyncAt: this.online ? Date.now() : null,
      pendingCount: this.queue.length,
      failedCount: this.queue.filter((a) => a.retryCount > 0).length,
    }
  }

  clearQueue(): void {
    this.queue = []
    this.persistQueue()
  }

  onStatusChange(listener: OfflineListener): () => void {
    this.statusListeners.add(listener)
    return () => this.statusListeners.delete(listener)
  }

  destroy(): void {
    this.statusListeners.clear()
  }
}
