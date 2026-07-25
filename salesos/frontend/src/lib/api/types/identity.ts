export interface UserProfile {
 id: string;
 email: string;
 full_name: string;
 full_name_ar: string | null;
 role: string;
 is_active: boolean;
 is_verified: boolean;
 tenant_id: string;
 created_at: string;
 updated_at: string;
}
