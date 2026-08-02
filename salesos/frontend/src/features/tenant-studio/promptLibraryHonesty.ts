/** Honesty copy for tip Prompt Library Studio (FE-S12-01). */
export const PROMPT_LIBRARY_HONESTY =
  "Tip /api/v1/studio/prompt-library — in-memory CAP-089 Prompt Library " +
  "extending CAP-023 shape. feature_ai_copilot remains False. " +
  "Live LLM execution / RAG GO / Marketplace prompt-pack install not claimed.";

export const PROMPT_LIBRARY_NON_GOALS = [
  "live LLM / enabling feature_ai_copilot",
  "RAG GO / Production GO",
  "Postgres persistence invent",
  "Marketplace prompt-pack install invent",
] as const;
