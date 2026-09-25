export interface CommercialEvidenceItem {
  id: string;
  evidence_type: string;
  source_domain: string;
  source_type: string;
  source_id: string;
  source_name: string;
  description: string;
  confidence: number;
  confidence_level: string;
  evidence_kind: string | null;
  recorded_at: string | null;
}

export interface CommercialInsight {
  id: string;
  category: string;
  title: string;
  description: string;
  target_id: string;
  target_type: string;
  overall_confidence: number;
  confidence_level: string;
  created_at: string | null;
  updated_at: string | null;
  evidence_items: CommercialEvidenceItem[];
}

export interface CommercialEvidenceResponse {
  items: CommercialInsight[];
  total: number;
  page: number;
  page_size: number;
  read_only: true;
}
