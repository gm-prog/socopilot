import { useEffect, useState } from "react";
import { fetchOllamaStatus, fetchReadiness } from "../api/client";
import { EliteCard } from "../components/EliteCard";

function StatusBadge({ status }: { status: string }) {
  const colors: Record<string, string> = {
    ok: "text-heritage-emerald border-heritage-emerald/50 bg-heritage-emerald/10",
    fail: "text-heritage-burgundy border-heritage-burgundy/50 bg-heritage-burgundy/10",
    degraded: "text-heritage-warning border-heritage-warning/50 bg-heritage-warning/10",
  };
  const cls = colors[status] || "text-heritage-muted border-heritage-goldBorder/30 bg-heritage-ink/70";
  return (
    <span className={`inline-flex items-center px-3 py-1 text-xs font-sans tracking-widest uppercase border rounded-full ${cls}`}>{status}</span>
  );
}

export default function Status() {
  const [ready, setReady] = useState<Awaited<ReturnType<typeof fetchReadiness>> | null>(null);
  const [ollama, setOllama] = useState<Record<string, unknown> | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([fetchReadiness(), fetchOllamaStatus()])
      .then(([r, o]) => {
        setReady(r);
        setOllama(o);
      })
      .catch((e) => setError(e instanceof Error ? e.message : "Unknown error"));
  }, []);

  return (
    <div className="flex flex-col h-full gap-6">
      <div>
        <h2 className="text-3xl font-serif text-heritage-gold tracking-wide mb-2">System Status</h2>
        <p className="text-heritage-muted text-sm font-sans tracking-widest uppercase">
          Readiness probes for all Phase 0 dependencies
        </p>
      </div>

      {error && (
        <div className="rounded-3xl border border-heritage-burgundy/30 bg-heritage-burgundy/10 px-6 py-4 text-sm font-sans tracking-wide">
          <span className="text-heritage-burgundy">{error}</span>
        </div>
      )}

      <EliteCard className="overflow-hidden">
        <div className="px-6 py-4 border-b border-heritage-goldBorder/30 flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <h3 className="font-serif text-heritage-gold text-lg tracking-wide">Readiness Checks</h3>
          {ready && <StatusBadge status={ready.status} />}
        </div>
        <table className="w-full text-sm">
          <thead>
            <tr className="text-heritage-muted text-left border-b border-heritage-goldBorder/20">
              <th className="px-6 py-3 font-medium font-sans tracking-widest uppercase">Service</th>
              <th className="px-6 py-3 font-medium font-sans tracking-widest uppercase">Status</th>
              <th className="px-6 py-3 font-medium font-sans tracking-widest uppercase">Detail</th>
            </tr>
          </thead>
          <tbody>
            {Object.entries(ready?.checks || {}).map(([name, status]) => (
              <tr key={name} className="border-b border-heritage-goldBorder/10 last:border-0">
                <td className="px-6 py-3 font-mono text-heritage-text">{name}</td>
                <td className="px-6 py-3">
                  <StatusBadge status={status} />
                </td>
                <td className="px-6 py-3 text-heritage-muted text-xs font-sans tracking-wide">—</td>
              </tr>
            ))}
            {!ready && (
              <tr>
                <td colSpan={3} className="px-6 py-4 text-heritage-muted font-sans tracking-wide">
                  Loading...
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </EliteCard>

      <EliteCard className="p-6 flex-1 overflow-auto">
        <h3 className="font-serif text-heritage-gold text-lg mb-4 tracking-wide">Ollama</h3>
        <pre className="text-xs font-mono text-heritage-text overflow-auto">
          {ollama ? JSON.stringify(ollama, null, 2) : "Loading..."}
        </pre>
      </EliteCard>
    </div>
  );
}
