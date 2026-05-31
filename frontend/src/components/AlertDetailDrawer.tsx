import { useEffect, useState } from "react";
import {
  fetchAlert,
  fetchAlertEnrichment,
  updateAlertWorkflow,
} from "../api/alerts";
import type { AlertDetail, EnrichmentResult } from "../types/alert";
import EnrichmentBadge from "./EnrichmentBadge";
import { EliteCard } from "./EliteCard";

const LIFECYCLE = ["new", "triaged", "investigating", "contained", "resolved", "false_positive"];

interface Props {
  alertId: string | null;
  onClose: () => void;
}

export default function AlertDetailDrawer({ alertId, onClose }: Props) {
  const [alert, setAlert] = useState<AlertDetail | null>(null);
  const [enrichment, setEnrichment] = useState<EnrichmentResult[]>([]);
  const [tab, setTab] = useState<"normalized" | "raw" | "timeline">("normalized");
  const [notes, setNotes] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const load = async (id: string) => {
    setLoading(true);
    setError(null);
    try {
      const [a, e] = await Promise.all([fetchAlert(id), fetchAlertEnrichment(id)]);
      setAlert(a);
      setEnrichment(e);
      setNotes(a.analyst_notes || "");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (!alertId) {
      setAlert(null);
      return;
    }
    load(alertId);
  }, [alertId]);

  const handleLifecycle = async (state: string) => {
    if (!alertId) return;
    const updated = await updateAlertWorkflow(alertId, { lifecycle_state: state });
    setAlert(updated);
  };

  const handleSaveNotes = async () => {
    if (!alertId) return;
    const updated = await updateAlertWorkflow(alertId, { analyst_notes: notes });
    setAlert(updated);
  };

  if (!alertId) return null;

  const abuseSummary = alert?.enrichment_summary?.providers as Record<
    string,
    { abuse_confidence?: number }
  > | undefined;

  return (
    <div className="fixed inset-0 z-50 flex justify-end">
      <div className="absolute inset-0 bg-heritage-ink/80 backdrop-blur-sm" onClick={onClose} />
      <aside className="relative w-full max-w-2xl h-full overflow-hidden bg-heritage-surface border-l border-heritage-goldBorder shadow-2xl transition duration-500 ease-premium">
        <header className="flex items-center justify-between gap-4 px-6 py-5 border-b border-heritage-goldBorder/30">
          <div className="space-y-1">
            <p className="text-xs uppercase tracking-[0.32em] text-heritage-muted">Intelligence Inspector</p>
            <h2 className="text-2xl font-serif text-heritage-gold leading-none">{alert?.title || "Alert Details"}</h2>
          </div>
          <button type="button" onClick={onClose} className="text-heritage-muted hover:text-heritage-gold text-3xl transition-colors duration-400 ease-premium">
            ×
          </button>
        </header>

        <div className="flex-1 overflow-auto p-6 space-y-6">
          {loading && <p className="text-heritage-muted text-sm font-sans tracking-wide">Loading intelligence...</p>}
          {error && <p className="text-heritage-burgundy text-sm font-sans tracking-wide">{error}</p>}

          {alert && (
            <div className="space-y-6">
              <div className="grid gap-4 lg:grid-cols-[1fr_220px]">
                <div className="space-y-4">
                  <div className="flex flex-wrap items-center gap-3">
                    <span className="rounded-full border px-3 py-1 text-xs uppercase tracking-[0.32em] text-heritage-text border-heritage-gold/30 bg-heritage-gold/10">
                      {alert.severity}
                    </span>
                    <span className="rounded-full border px-3 py-1 text-xs uppercase tracking-[0.32em] text-heritage-muted border-heritage-goldBorder/30 bg-heritage-ink/70">
                      {alert.lifecycle_state.replace("_", " ")}
                    </span>
                    {alert.duplicate_count > 1 && (
                      <span className="text-xs uppercase tracking-[0.28em] text-heritage-gold">{alert.duplicate_count} occurrences</span>
                    )}
                  </div>

                  <div className="grid gap-4 sm:grid-cols-2">
                    <EliteCard className="p-4">
                      <p className="text-[11px] uppercase tracking-[0.28em] text-heritage-muted">Source</p>
                      <p className="mt-3 text-sm text-heritage-text">{alert.source}</p>
                    </EliteCard>
                    <EliteCard className="p-4">
                      <p className="text-[11px] uppercase tracking-[0.28em] text-heritage-muted">Detected</p>
                      <p className="mt-3 text-sm text-heritage-text">{new Date(alert.detected_at).toLocaleString()}</p>
                    </EliteCard>
                  </div>
                </div>

                <div className="space-y-3">
                  <div className="rounded-3xl border border-heritage-goldBorder/20 bg-heritage-glass p-4">
                    <p className="text-[11px] uppercase tracking-[0.28em] text-heritage-muted">Alert Stream</p>
                    <p className="mt-3 text-sm text-heritage-text">{alert.title}</p>
                  </div>
                  {abuseSummary?.abuseipdb && (
                    <EnrichmentBadge
                      provider="abuseipdb"
                      status="success"
                      score={abuseSummary.abuseipdb.abuse_confidence}
                    />
                  )}
                </div>
              </div>

              <div className="space-y-4">
                <div className="flex flex-wrap gap-3">
                  {LIFECYCLE.map((s) => (
                    <button
                      key={s}
                      type="button"
                      onClick={() => handleLifecycle(s)}
                      className={`rounded-full px-4 py-2 text-xs uppercase tracking-[0.22em] transition duration-300 ease-premium ${
                        alert.lifecycle_state === s
                          ? "bg-heritage-gold/15 border border-heritage-gold text-heritage-gold"
                          : "border border-heritage-goldBorder/25 text-heritage-muted hover:border-heritage-gold/50 hover:text-heritage-text"
                      }`}
                    >
                      {s.replace("_", " ")}
                    </button>
                  ))}
                </div>

                <EliteCard className="p-5">
                  <h3 className="text-sm font-serif text-heritage-gold tracking-wide">Indicators of Compromise ({alert.iocs?.length || 0})</h3>
                  <div className="max-h-52 overflow-auto border border-heritage-goldBorder/30 bg-heritage-ink/70 mt-4">
                    <table className="w-full text-xs font-mono">
                      <tbody>
                        {(alert.iocs || []).map((ioc) => (
                          <tr key={ioc.id} className="border-b border-heritage-goldBorder/20 last:border-0">
                            <td className="px-3 py-2 text-heritage-gold font-sans tracking-widest uppercase">{ioc.ioc_type}</td>
                            <td className="px-3 py-2 truncate text-heritage-text">{ioc.ioc_value}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </EliteCard>
              </div>

              <EliteCard className="p-5">
                <div className="flex items-center justify-between gap-4">
                  <h3 className="text-sm font-serif text-heritage-gold tracking-wide">Analyst Notes</h3>
                  <button
                    type="button"
                    onClick={handleSaveNotes}
                    className="rounded-full border border-heritage-gold/30 px-4 py-2 text-xs uppercase tracking-[0.22em] text-heritage-gold hover:bg-heritage-gold/10 transition duration-300 ease-premium"
                  >
                    Save
                  </button>
                </div>
                <textarea
                  className="mt-4 w-full min-h-[120px] rounded-3xl border border-heritage-goldBorder/25 bg-heritage-ink/80 p-4 text-sm text-heritage-text font-sans focus:border-heritage-gold/50 focus:outline-none transition duration-300 ease-premium"
                  value={notes}
                  onChange={(e) => setNotes(e.target.value)}
                />
              </EliteCard>

              <div className="space-y-4">
                <div className="flex gap-3 border-b border-heritage-goldBorder/30 pb-3">
                  {(["normalized", "raw", "timeline"] as const).map((t) => (
                    <button
                      key={t}
                      type="button"
                      onClick={() => setTab(t)}
                      className={`text-xs uppercase tracking-[0.28em] transition duration-300 ease-premium ${
                        tab === t ? "border-b-2 border-heritage-gold text-heritage-gold pb-2" : "text-heritage-muted hover:text-heritage-text"
                      }`}
                    >
                      {t}
                    </button>
                  ))}
                </div>
                <EliteCard className="p-4 overflow-auto">
                  <pre className="whitespace-pre-wrap text-xs font-mono text-heritage-text">
                    {JSON.stringify(
                      tab === "normalized"
                        ? alert.normalized_payload
                        : tab === "raw"
                          ? alert.raw_payload || {}
                          : {
                              detected: alert.detected_at,
                              ingested: alert.ingested_at,
                              lifecycle: alert.lifecycle_state,
                              enrichment: alert.enrichment_summary,
                            },
                      null,
                      2,
                    )}
                  </pre>
                </EliteCard>
              </div>
            </div>
          )}
        </div>
      </aside>
    </div>
  );
}
