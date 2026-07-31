import { useMemo } from "react";
import type { NBAFeedItem } from "@salesos/widget-sdk";

export function useNBAFeed(): NBAFeedItem[] {
  return useMemo(() => [], []);
}
