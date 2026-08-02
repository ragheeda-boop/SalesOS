/** Honesty copy for tip AI Outreach (FE-S11-08). */
export const OUTREACH_HONESTY =
  "Tip /api/v1/gtm/outreach — FixtureOutreachGenerator + governed prompt " +
  "gtm.ai_outreach.v1 (platform LLM spend path). delivery_status=draft_only. " +
  "feature_ai_copilot remains False. Live LLM / SMTP / LinkedIn / WhatsApp / RAG GO not claimed.";

export const OUTREACH_NON_GOALS = [
  "live SMTP / mailbox delivery",
  "LinkedIn / WhatsApp channels",
  "enabling feature_ai_copilot / live OpenAI-Claude inference",
  "Production GO / RAG GO",
] as const;
