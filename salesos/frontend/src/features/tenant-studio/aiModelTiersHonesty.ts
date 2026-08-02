/** Tip STORY-12-04 AI model tier Studio honesty.
 * Read-only entitlement catalog. feature_ai_copilot stays False.
 * Not Production GO / RAG GO.
 */

export const AI_MODEL_TIERS_HONESTY =
  "Tip GET /api/v1/studio/ai-model-tiers (+ /catalog, /defaults). Maps Plan.entitlements.ai_model_tier → catalog provider/model ids. Read-only — no PUT. feature_ai_copilot remains False unless explicitly enabled; live LLM product path not claimed.";

export const AI_MODEL_TIERS_NON_GOALS = [
  "Invented PUT/write for ai_model_tier",
  "Enabling feature_ai_copilot / live LLM routing",
  "Website Intelligence / AI Outreach (STORY-11-07/08)",
  "Prompt Library / Policies / Memory (12-01..12-03)",
] as const;
