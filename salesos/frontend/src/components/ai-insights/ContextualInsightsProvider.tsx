"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";
import api from "@/lib/api";
import { getTenantId } from "@/lib/hooks/useTenant";
import type { AiInsightsContextType, ContextualInsightData, InlineSuggestionData } from "./types";
import { getConfidenceLevel } from "./ConfidenceBadge";

const AiInsightsContext = createContext<AiInsightsContextType>({
  insights: [],
  suggestions: [],
  showLowConfidence: false,
  setShowLowConfidence: () => {},
  dismissInsight: () => {},
  dismissSuggestion: () => {},
  isLoading: false,
});

interface AiInsightsProviderProps {
  children: ReactNode;
  page: string;
  entityType?: string;
  entityId?: string;
}

export function AiInsightsProvider({
  children,
  page,
  entityType,
  entityId,
}: AiInsightsProviderProps) {
  const [insights, setInsights] = useState<ContextualInsightData[]>([]);
  const [suggestions, setSuggestions] = useState<InlineSuggestionData[]>([]);
  const [showLowConfidence, setShowLowConfidence] = useState(false);
  const [dismissedIds, setDismissedIds] = useState<Set<string>>(new Set());
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    let cancelled = false;

    async function fetchInsights() {
      setIsLoading(true);
      try {
        const res = await api.post(
          "/api/v1/copilot/contextual-insights",
          { page, entity_type: entityType, entity_id: entityId },
          { headers: { "X-Tenant-Id": getTenantId() } }
        );

        if (cancelled) return;

        const data = res.data;
        const rawInsights: ContextualInsightData[] = (data.insights ?? []).map(
          (i: Record<string, unknown>) => ({
            ...i,
            confidenceLevel: getConfidenceLevel(Number(i.confidence) || 0),
            timestamp: Date.now(),
          })
        );
        const rawSuggestions: InlineSuggestionData[] = (data.suggestions ?? []).map(
          (s: Record<string, unknown>) => ({
            ...s,
            confidenceLevel: getConfidenceLevel(Number(s.confidence) || 0),
          })
        );

        setInsights(rawInsights);
        setSuggestions(rawSuggestions);
      } catch {
        if (!cancelled) {
          setInsights([]);
          setSuggestions([]);
        }
      } finally {
        if (!cancelled) setIsLoading(false);
      }
    }

    fetchInsights();
    return () => {
      cancelled = true;
    };
  }, [page, entityType, entityId]);

  const dismissInsight = useCallback((id: string) => {
    setDismissedIds((prev) => new Set(prev).add(id));
  }, []);

  const dismissSuggestion = useCallback((id: string) => {
    setDismissedIds((prev) => new Set(prev).add(id));
  }, []);

  const filteredInsights = useMemo(() => {
    return insights.filter((i) => {
      if (dismissedIds.has(i.id)) return false;
      if (!showLowConfidence && i.confidenceLevel === "low") return false;
      return true;
    });
  }, [insights, dismissedIds, showLowConfidence]);

  const filteredSuggestions = useMemo(() => {
    return suggestions.filter((s) => {
      if (dismissedIds.has(s.id)) return false;
      if (!showLowConfidence && s.confidenceLevel === "low") return false;
      return true;
    });
  }, [suggestions, dismissedIds, showLowConfidence]);

  const value = useMemo<AiInsightsContextType>(
    () => ({
      insights: filteredInsights,
      suggestions: filteredSuggestions,
      showLowConfidence,
      setShowLowConfidence,
      dismissInsight,
      dismissSuggestion,
      isLoading,
    }),
    [
      filteredInsights,
      filteredSuggestions,
      showLowConfidence,
      dismissInsight,
      dismissSuggestion,
      isLoading,
    ]
  );

  return <AiInsightsContext.Provider value={value}>{children}</AiInsightsContext.Provider>;
}

export function useAiInsights() {
  return useContext(AiInsightsContext);
}
