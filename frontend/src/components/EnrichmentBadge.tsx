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
  const cls = isBad
    ? "bg-red-500/20 text-red-300 border-red-500/40"
    : isGood
      ? "bg-green-500/20 text-green-300 border-green-500/40"
      : "bg-yellow-500/20 text-yellow-300 border-yellow-500/40";

  return (
    <span className={`px-2 py-0.5 rounded text-xs font-mono border ${cls}`}>
      {provider}
      {score !== undefined ? ` (${score}%)` : ` [${status}]`}
    </span>
  );
}
