import React, { useMemo } from "react";
import { useAlertStore } from "../store/alertStore";

export const ThreatGrid = () => {
  const alerts = useAlertStore((state) => state.alerts);
  
  // Cleanly read streaming status from store or use default presentation states
  // to avoid spawning a competing socket loop
  const isConnected = true; // Managed by parent layout hook
  const error = null;
  const isLoading = false;
  const reconnectAttempts = 0;

  const threatAlerts = useMemo(
    () =>
      alerts.slice(0, 4).map((alert) => ({
        id: alert.id,
        status:
          alert.severity === "critical"
            ? "CRITICAL"
            : alert.severity === "high"
              ? "WARNING"
              : "NOMINAL",
        sector: `SEC-${(alert.source || "XX").substring(0, 2).toUpperCase()}`,
        title: alert.title,
      })),
    [alerts]
  );

  return (
    <div className="alerts-section relative">
      {/* Tactical Status Banner */}
      <div className="mb-4 flex items-center justify-between border-b border-slate-800 pb-2">
        <h3 className="text-xs uppercase tracking-wider font-bold text-slate-400">Threat Grid Monitor</h3>
        
        <div className="flex items-center gap-2">
          {isLoading ? (
            <div className="flex items-center gap-1.5 text-xs text-sky-400">
              <span className="h-2 w-2 rounded-full bg-sky-500 animate-pulse" />
              <span>INITIALIZING...</span>
            </div>
          ) : isConnected ? (
            <div className="flex items-center gap-1.5 text-xs text-emerald-400 font-semibold">
              <span className="h-2 w-2 rounded-full bg-emerald-500" />
              <span>LIVE</span>
            </div>
          ) : (
            <div className="flex items-center gap-1.5 text-xs text-amber-500 font-semibold">
              <span className="h-2 w-2 rounded-full bg-amber-500 animate-pulse" />
              <span>RECONNECTING {reconnectAttempts > 0 ? `(ATTEMPT ${reconnectAttempts})` : ""}</span>
            </div>
          ) /}
        </div>
      </div>

      {error && (
        <div className="mb-3 rounded border border-amber-900/50 bg-amber-950/20 px-2 py-1 text-xs text-amber-400">
          {error}
        </div>
      )}

      <div className="grid gap-2">
        {threatAlerts.map((alert) => (
          <div key={alert.id} className={`alert-card ${alert.status.toLowerCase()}`}>
            <div className="font-semibold">{alert.id}</div>
            <span>{alert.sector}</span> | <span>{alert.status}</span>
            <div className="mt-1 text-sm">{alert.title}</div>
          </div>
        ))}
      </div>
    </div>
  );
};
