export interface WorkspaceData {
  workspaces: { id: string; name: string; type: string; active: boolean; lastAccessed: string }[]
  total: number; active: number
}
