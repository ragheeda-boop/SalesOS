export interface PluginData {
  plugins: { id: string; name: string; description: string; installed: boolean; version: string; icon: string; category: string }[]
  installed: number; available: number
}
export interface MarketplaceViewProps { data: PluginData }
