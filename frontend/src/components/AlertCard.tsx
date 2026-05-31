import { EliteCard } from "./EliteCard";
import { colors } from "../styles/tokens";

type Severity = "critical" | "high" | "medium" | "low";

const severityAccent: Record<Severity, string> = {
  critical: colors.accent.gold,
  high: colors.accent.burgundy,
  medium: colors.accent.emerald,
  low: colors.accent.navy,
};

interface AlertCardProps {
  id: string;
  title: string;
  source: string;
  time: string;
  status: string;
  severity: Severity;
  duplicateCount: number;
  onClick: () => void;
}

export function AlertCard({
  title,
  source,
  time,
  status,
  severity,
  duplicateCount,
  onClick,
}: AlertCardProps) {
  return (
    <button
      type="button"
      onClick={onClick}
      className="w-full text-left"
    >
      <EliteCard className="space-y-4 hover:-translate-y-0.5 focus-visible:outline heritage-focus-ring">
        <div className="flex items-start justify-between gap-4">
          <div>
            <div className="flex items-center gap-3">
              <span
                className="h-3.5 w-3.5 rounded-full"
                style={{ backgroundColor: severityAccent[severity] }}
              />
              <span className="text-xs uppercase tracking-[0.28em] text-heritage-muted">
                {severity}
              </span>
            </div>
            <h3 className="mt-3 text-lg font-semibold text-heritage-primary">
              {title}
            </h3>
          </div>

          <div className="space-y-2 text-right">
            <div className="rounded-full bg-heritage-glow px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.32em] text-heritage-muted">
              {status}
            </div>
            <p className="text-xs text-heritage-muted">{time}</p>
          </div>
        </div>

        <div className="grid gap-3 sm:grid-cols-2">
          <div className="rounded-2xl border border-heritage-glow/30 bg-white/3 p-3">
            <p className="text-[11px] uppercase tracking-[0.24em] text-heritage-muted">
              Source
            </p>
            <p className="mt-2 text-sm text-heritage-primary">{source}</p>
          </div>
          <div className="rounded-2xl border border-heritage-glow/30 bg-white/3 p-3">
            <p className="text-[11px] uppercase tracking-[0.24em] text-heritage-muted">
              Enrichment
            </p>
            <p className="mt-2 text-sm text-heritage-primary">{duplicateCount} linked alerts</p>
          </div>
        </div>
      </EliteCard>
    </button>
  );
}
