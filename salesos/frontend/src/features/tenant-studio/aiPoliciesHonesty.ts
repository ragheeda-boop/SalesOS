export const AI_POLICIES_HONESTY =
  "Tip /api/v1/studio/ai-policies — in-memory CAP-091 AI Policies " +
  "reusing AI-GR-* guardrails (toggles + data-class → model-tier ceilings + evaluate). " +
  "feature_ai_copilot remains False; live LLM / RAG GO not claimed.";

export const AI_POLICIES_NON_GOALS = [
  "Live LLM / enabling feature_ai_copilot",
  "RAG GO / Production GO",
  "Inventing new guardrail implementations",
  "AI Memory (STORY-12-03)",
];
