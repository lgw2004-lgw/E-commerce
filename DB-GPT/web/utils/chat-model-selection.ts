/** Preserve a user's choice while the registry changes; replace unavailable models. */
export function reconcileChatModel(current: string, available: readonly string[]): string {
  return available.includes(current) ? current : (available[0] ?? '');
}
