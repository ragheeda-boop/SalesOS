/** Tip STORY-12-04 AI model tier Studio honesty.
 * Plan entitlements can be edited by platform admins; feature_ai_copilot stays False.
 * Not Production GO / RAG GO.
 */

export const AI_MODEL_TIERS_HONESTY =
  "Plan AI tier defaults are saved through the owner-only plan entitlement API; tenant resolution shows the enforced result. This does not enable feature_ai_copilot or connect a live model provider.";

export const AI_MODEL_TIERS_NON_GOALS = [
  "Enabling feature_ai_copilot / live LLM routing",
  "Website Intelligence / AI Outreach (STORY-11-07/08)",
  "Prompt Library / Policies / Memory (12-01..12-03)",
] as const;
