"use client";

export type ConfidenceLevel = "high" | "medium" | "low";

export interface ContextualInsightData {
  id: string;
  page: string;
  title: string;
  content: string;
  confidence: number;
  confidenceLevel: ConfidenceLevel;
  suggestion?: string;
  action?: { label: string; href: string };
  entityType?: string;
  entityId?: string;
  timestamp: number;
}

export interface InlineSuggestionData {
  id: string;
  target: string;
  content: string;
  confidence: number;
  confidenceLevel: ConfidenceLevel;
  page: string;
}

export interface AiInsightsContextType {
  insights: ContextualInsightData[];
  suggestions: InlineSuggestionData[];
  showLowConfidence: boolean;
  setShowLowConfidence: (v: boolean) => void;
  dismissInsight: (id: string) => void;
  dismissSuggestion: (id: string) => void;
  isLoading: boolean;
}
