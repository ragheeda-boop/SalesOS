/** Honesty copy for tip Website Intelligence (FE-S11-07). */
export const WEBSITE_INTEL_HONESTY =
  "Tip /api/v1/gtm/website-intelligence — FixtureWebsiteAnalyzer + governed " +
  "prompt gtm.website_intelligence.v1 (platform LLM spend path). " +
  "feature_ai_copilot remains False. Live crawl / live LLM / Claygent / RAG GO not claimed.";

export const WEBSITE_INTEL_NON_GOALS = [
  "live website crawl or scraping network",
  "enabling feature_ai_copilot / live OpenAI-Claude inference",
  "Claygent / Clay vendor integration",
  "FE-S11-08 AI Outreach invent",
  "Production GO / RAG GO",
] as const;
