import { severityBadgeClass } from '../utils/badgeStyles';

export default function SeverityBadge({ severity }: { severity: string }) {
  const cls = severityBadgeClass(severity);
  return (
    <span className={`px-2 py-0.5 rounded text-xs font-mono border uppercase ${cls}`}>
      {severity}
    </span>
  );
}
