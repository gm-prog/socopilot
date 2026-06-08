import { badgeColorClass } from '../utils/badgeStyles';

export default function EnrichmentBadge({
  provider,
  status,
  score,
}: {
  provider: string;
  status: string;
  score?: number;
}) {
  const isGood = status === "success" && (score === undefined || score < 30);
  const isBad = score !== undefined && score >= 70;
  const cls = badgeColorClass(isBad ? 'red' : isGood ? 'green' : 'yellow');

  return (
    <span className={`px-2 py-0.5 rounded text-xs font-mono border ${cls}`}>
      {provider}
      {score !== undefined ? ` (${score}%)` : ` [${status}]`}
    </span>
  );
}
