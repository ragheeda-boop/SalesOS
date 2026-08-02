/** Tip STORY-08-06 ConflictResolutionPolicy.default() mirrors (honesty only).
 * Not Production GO. Unlinked badges on tip Monitor (FE-S09-08).
 */

export const TIP_SALESOS_AUTHORED_FIELDS = [
  "risk_score",
  "ai_sentiment",
  "ai_score",
] as const;

export const TIP_OPERATIONAL_FIELDS = [
  "name",
  "email",
  "phone",
  "cr_number",
  "stage",
  "amount",
  "currency",
] as const;

/** Tip default rules from ConflictResolutionPolicy.default(). */
export function tipDefaultConflictRules(): Array<{
  internal: string;
  winner: "source" | "salesos";
  exclude_from_pull: boolean;
}> {
  const authored = TIP_SALESOS_AUTHORED_FIELDS.map((internal) => ({
    internal,
    winner: "salesos" as const,
    exclude_from_pull: true,
  }));
  const operational = TIP_OPERATIONAL_FIELDS.map((internal) => ({
    internal,
    winner: "source" as const,
    exclude_from_pull: false,
  }));
  return [...authored, ...operational];
}
