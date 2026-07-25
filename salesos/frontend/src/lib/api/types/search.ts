export interface SearchResultItem {
 id: string;
 type: string;
 score: number;
 data: Record<string, unknown>;
 matched_fields?: string[];
 explanation?: string;
}

export interface SearchResponse {
 query: string;
 strategy: string;
 total: number;
 took_ms: number;
 items: SearchResultItem[];
 facets?: Record<string, Record<string, number>>;
 suggestions?: string[];
}

export interface SearchParams {
 q: string;
 strategy?:"fulltext" |"semantic" |"graph" |"hybrid";
 limit?: number;
 offset?: number;
 include_facets?: boolean;
 city?: string;
 region?: string;
 industry?: string;
 status?: string;
}
