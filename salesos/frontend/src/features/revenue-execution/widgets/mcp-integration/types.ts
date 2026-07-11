export interface MCPData {
  connections: { id: string; name: string; type: string; status: 'connected' | 'disconnected' | 'error'; lastSync?: string; entities: number }[]
  totalConnections: number; activeConnections: number; syncedEntities: number
}
