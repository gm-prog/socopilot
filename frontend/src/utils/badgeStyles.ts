const BADGE_COLORS = {
  slate: 'bg-slate-500/20 text-slate-300 border-slate-500/40',
  blue: 'bg-blue-500/20 text-blue-300 border-blue-500/40',
  yellow: 'bg-yellow-500/20 text-yellow-300 border-yellow-500/40',
  orange: 'bg-orange-500/20 text-orange-300 border-orange-500/40',
  red: 'bg-red-500/20 text-red-300 border-red-500/40',
  green: 'bg-green-500/20 text-green-300 border-green-500/40',
} as const;

export type BadgeColor = keyof typeof BADGE_COLORS;

export function badgeColorClass(color: BadgeColor): string {
  return BADGE_COLORS[color];
}

const SEVERITY_COLOR_MAP: Record<string, BadgeColor> = {
  informational: 'slate',
  low: 'blue',
  medium: 'yellow',
  high: 'orange',
  critical: 'red',
};

export function severityBadgeClass(severity: string): string {
  const color = SEVERITY_COLOR_MAP[severity.toLowerCase()];
  return BADGE_COLORS[color ?? 'yellow'];
}
