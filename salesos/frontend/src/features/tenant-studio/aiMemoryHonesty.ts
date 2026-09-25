export const AI_MEMORY_HONESTY =
  "Tip /api/v1/studio/ai-memory — tenant-scoped PostgreSQL CAP-063 conversation memory " +
  "with encrypted turns, opt-in settings, retention, and delete. Cross-session long-term " +
  "deferred. feature_ai_copilot remains False; live LLM / RAG GO not claimed. " +
  "Persistence requires the dedicated AI_MEMORY_ENCRYPTION_KEY.";

export const AI_MEMORY_NON_GOALS = [
  "Cross-session long-term memory",
  "Live LLM / enabling feature_ai_copilot",
  "RAG GO / Production GO",
  "Managed KMS or automatic encryption-key rotation",
];
