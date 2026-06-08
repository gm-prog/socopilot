import type { Severity, AlertState } from '../store/types';

export const SEV_ORDER: Record<Severity, number> = {
  CRITICAL: 0,
  HIGH: 1,
  MEDIUM: 2,
  LOW: 3,
  INFO: 4,
};

export const ANALYSTS: Record<string, { initials: string; color: string }> = {
  'A. Reed': { initials: 'AR', color: '#7c3aed' },
  'J. Chen': { initials: 'JC', color: '#2563eb' },
  'M. Okafor': { initials: 'MO', color: '#059669' },
  'S. Patel': { initials: 'SP', color: '#b45309' },
};

export function formatStateLabel(state: AlertState | string): string {
  return state.replace(/_/g, ' ');
}

export function formatAnalyst(analyst: string | null): string {
  if (!analyst) return 'Unassigned';
  const parts = analyst.split(' ');
  return parts.length > 1 ? parts[1] : analyst;
}

export function compareSeverity(a: Severity, b: Severity): number {
  return SEV_ORDER[a] - SEV_ORDER[b];
}
