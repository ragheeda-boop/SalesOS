export interface RealtimeSubscription {
  id: string
  channel: string
  event: string
  callback: (data: unknown) => void
  unsubscribe: () => void
}

type ConnectionStatus = 'disconnected' | 'connecting' | 'connected' | 'error'

type ConnectionListener = (status: ConnectionStatus) => void
type MessageHandler = (channel: string, event: string, data: unknown) => void

interface PendingSubscription {
  channel: string
  event: string
  callback: (data: unknown) => void
}

export class RealtimeRuntime {
  private ws: WebSocket | null = null
  private url: string
  private subscriptions = new Map<string, PendingSubscription[]>()
  private connectionListeners = new Set<ConnectionListener>()
  private messageHandlers = new Set<MessageHandler>()
  private status: ConnectionStatus = 'disconnected'
  private reconnectAttempts = 0
  private maxReconnectAttempts = 10
  private reconnectDelay = 1000
  private token: string | null = null
  private subscriptionCounter = 0

  constructor(url: string) {
    this.url = url
  }

  setToken(token: string) {
    this.token = token
  }

  connect(token?: string): void {
    if (this.status === 'connecting' || this.status === 'connected') return
    if (token) this.token = token
    this.setStatus('connecting')
    try {
      const wsUrl = this.token ? `${this.url}?token=${this.token}` : this.url
      this.ws = new WebSocket(wsUrl)
      this.ws.onopen = () => {
        this.setStatus('connected')
        this.reconnectAttempts = 0
        this.resubscribeAll()
      }
      this.ws.onmessage = (event) => {
        try {
          const msg = JSON.parse(event.data)
          const { channel, event: evt, data } = msg
          this.messageHandlers.forEach((h) => h(channel, evt, data))
          const subs = this.subscriptions.get(channel)
          if (subs) {
            subs.filter((s) => s.event === evt).forEach((s) => s.callback(data))
          }
        } catch (e) {
          console.warn('[RealtimeRuntime] Failed to process WebSocket message:', e)
        }
      }
      this.ws.onclose = () => {
        this.setStatus('disconnected')
        this.handleReconnect()
      }
      this.ws.onerror = () => {
        this.setStatus('error')
      }
    } catch {
      this.setStatus('error')
    }
  }

  disconnect(): void {
    this.ws?.close()
    this.ws = null
    this.setStatus('disconnected')
  }

  subscribe(channel: string, event: string, callback: (data: unknown) => void): RealtimeSubscription {
    const id = `sub_${++this.subscriptionCounter}`
    const pending: PendingSubscription = { channel, event, callback }
    if (!this.subscriptions.has(channel)) {
      this.subscriptions.set(channel, [])
    }
    this.subscriptions.get(channel)!.push(pending)
    if (this.status === 'connected') {
      this.sendSubscribe(channel)
    }
    return {
      id,
      channel,
      event,
      callback,
      unsubscribe: () => this.unsubscribe(id, channel, event),
    }
  }

  private unsubscribe(id: string, channel: string, event: string): void {
    const subs = this.subscriptions.get(channel)
    if (subs) {
      const idx = subs.findIndex((s) => s.event === event)
      if (idx >= 0) subs.splice(idx, 1)
      if (subs.length === 0) this.subscriptions.delete(channel)
    }
    if (this.status === 'connected') {
      this.sendUnsubscribe(channel, event)
    }
  }

  onMessage(handler: MessageHandler): () => void {
    this.messageHandlers.add(handler)
    return () => this.messageHandlers.delete(handler)
  }

  onConnectionChange(listener: ConnectionListener): () => void {
    this.connectionListeners.add(listener)
    return () => this.connectionListeners.delete(listener)
  }

  getStatus(): ConnectionStatus {
    return this.status
  }

  private setStatus(status: ConnectionStatus) {
    this.status = status
    this.connectionListeners.forEach((fn) => fn(status))
  }

  private sendSubscribe(channel: string) {
    this.ws?.send(JSON.stringify({ type: 'subscribe', channel }))
  }

  private sendUnsubscribe(channel: string, event: string) {
    this.ws?.send(JSON.stringify({ type: 'unsubscribe', channel, event }))
  }

  private resubscribeAll() {
    for (const channel of this.subscriptions.keys()) {
      this.sendSubscribe(channel)
    }
  }

  private handleReconnect() {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) return
    this.reconnectAttempts++
    const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1)
    setTimeout(() => this.connect(), Math.min(delay, 30000))
  }
}
