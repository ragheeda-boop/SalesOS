export interface NotificationPreferences {
  email_notifications: boolean;
  app_notifications: boolean;
  opportunity_alerts: boolean;
  company_updates: boolean;
  weekly_summary: boolean;
}

export interface ApiKeyRecord {
  id: string;
  name: string;
  key_preview: string;
  created_at: string;
}
