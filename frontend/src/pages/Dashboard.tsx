import { useEffect, useState } from "react";
import { fetchHealth, fetchSystemInfo } from "../api/client";
import { apiUrl } from "../config/api";
import { EliteCard } from "../components/EliteCard";

export default function Dashboard() {
  const [health, setHealth] = useState<{ status: string; version: string } | null>(null);
  const [info, setInfo] = useState<Record<string, unknown> | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([fetchHealth(), fetchSystemInfo()])
      .then(([h, i]) => {
        setHealth(h);
        setInfo(i);
      })
      .catch((e) => setError(e instanceof Error ? e.message : "Unknown error"));
  }, []);

  const cards = [
    { label: "Alerts Ingested", value: "—", sub: "Phase 1" },
    { label: "Open Incidents", value: "—", sub: "Phase 4" },
    { label: "FP Rate", value: "—", sub: "Phase 6" },
    { label: "MTTT", value: "—", sub: "Phase 3" },
  ];

  return (
    <div className="flex flex-col h-full">
      <div className="mb-8">
        <h2 className="text-3xl font-serif text-heritage-gold tracking-wide mb-2">Intelligence Dashboard</h2>
        <p className="text-heritage-muted text-sm font-sans tracking-widest uppercase">
          Phase 2 — IOC extraction, threat enrichment, OpenSearch, workflow lifecycle
        </p>
      </div>

      {error && (
        <div className="rounded-3xl border border-heritage-burgundy/30 bg-heritage-burgundy/10 px-6 py-4 text-sm font-sans tracking-wide mb-6">
          <span className="text-heritage-burgundy">API unreachable ({apiUrl("/api/v1/health")}): {error}</span>
        </div>
      )}

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        {cards.map((c) => (
          <EliteCard key={c.label} className="p-6">
            <p className="text-xs text-heritage-muted font-sans tracking-widest uppercase">{c.label}</p>
            <p className="text-4xl font-serif font-semibold mt-3 text-heritage-gold">{c.value}</p>
            <p className="text-xs text-heritage-muted mt-2 font-sans tracking-wide">{c.sub}</p>
          </EliteCard>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 flex-1">
        <EliteCard className="p-6">
          <h3 className="font-serif text-heritage-gold text-lg mb-4 tracking-wide">Platform Status</h3>
          {health ? (
            <dl className="space-y-3 text-sm font-mono">
              <div className="flex justify-between">
                <dt className="text-heritage-muted">API</dt>
                <dd className="text-heritage-emerald">{health.status}</dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-heritage-muted">Version</dt>
                <dd className="text-heritage-text">{health.version}</dd>
              </div>
            </dl>
          ) : (
            <p className="text-heritage-muted text-sm font-sans tracking-wide">Loading...</p>
          )}
        </EliteCard>

        <EliteCard className="p-6">
          <h3 className="font-serif text-heritage-gold text-lg mb-4 tracking-wide">Configuration</h3>
          {info ? (
            <pre className="text-xs font-mono text-heritage-text overflow-auto max-h-40">
              {JSON.stringify(info, null, 2)}
            </pre>
          ) : (
            <p className="text-heritage-muted text-sm font-sans tracking-wide">Loading...</p>
          )}
        </EliteCard>
      </div>
    </div>
  );
}
