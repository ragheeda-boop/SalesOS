"use client";

import { useEffect, useState, useCallback } from "react";
import { useNBA, type NBARecommendation } from "./useNBA";
import { NBAWidgetView } from "./NBAWidgetView";

interface NBAWidgetContainerProps {
  opportunityId: string;
}

export function NBAWidgetContainer({ opportunityId }: NBAWidgetContainerProps) {
  const [recommendation, setRecommendation] =
    useState<NBARecommendation | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);
  const { getNBA, refreshNBA, acceptNBA, dismissNBA } = useNBA(opportunityId);

  const load = useCallback(async () => {
    setLoading(true);
    setError(false);
    try {
      const nba = await getNBA();
      setRecommendation(nba);
    } catch {
      setError(true);
    } finally {
      setLoading(false);
    }
  }, [getNBA]);

  useEffect(() => {
    load();
    // opportunityId: reload when the opportunity changes even if getNBA identity is stable
  }, [load, opportunityId]);

  const handleAccept = async () => {
    if (!recommendation) return;
    await acceptNBA(recommendation.id);
    setRecommendation((prev) =>
      prev ? { ...prev, status: "accepted" } : null,
    );
  };

  const handleDismiss = async () => {
    if (!recommendation) return;
    await dismissNBA(recommendation.id);
    setRecommendation(null);
  };

  const handleRefresh = async () => {
    setLoading(true);
    const nba = await refreshNBA();
    setRecommendation(nba);
    setLoading(false);
  };

  return (
    <NBAWidgetView
      recommendation={recommendation}
      loading={loading}
      error={error}
      onAccept={handleAccept}
      onDismiss={handleDismiss}
      onRefresh={handleRefresh}
      onRetry={load}
    />
  );
}
