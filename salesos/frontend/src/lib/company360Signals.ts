/** Safe count for the Company 360 signals badge when API omits signals/total. */
export function company360SignalsTotal(
  signals: { total?: number } | null | undefined
): number {
  return signals?.total ?? 0;
}
