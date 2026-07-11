export interface SecurityData {
  ssoEnabled: boolean; rbacEnabled: boolean; auditEnabled: boolean; mfaEnabled: boolean
  activeUsers: number; roles: number; auditEvents: number; pendingActions: number
  recentAudit: { action: string; user: string; timestamp: string; status: string }[]
}
