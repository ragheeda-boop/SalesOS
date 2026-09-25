export interface AIGovernanceAuditEvent {
  id: number;
  user_id: string | null;
  action: string;
  resource_type: string;
  resource_id: string | null;
  outcome: string;
  request_id: string | null;
  created_at: string | null;
  policy_name: string | null;
  decision: string | null;
  enforcement_action: string | null;
}

export interface AIGovernanceAuditResponse {
  items: AIGovernanceAuditEvent[];
  total: number;
  page: number;
  page_size: number;
  generated_at: string;
  read_only: true;
}
