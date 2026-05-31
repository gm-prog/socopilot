import React, { useMemo } from "react";
import { AlertTriangle, X, Database } from "lucide-react";
import { useAlertStore } from "../../store/alertStore";

export default function DataDeck() {
  const alerts = useAlertStore((state) => state.alerts);
  const selectedEntity = useAlertStore((state) => state.selectedEntity);
  const clearSelectedEntity = useAlertStore(
    (state) => state.clearSelectedEntity
  );

  const threatGridAlerts = useMemo(() => {
    return alerts.slice(0, 5).map((alert) => ({
      id: alert.id,
      sector: `SEC-${
        alert.source?.substring(0, 2).toUpperCase() || "XX"
      }`,
      metric: alert.source || "Unknown Source",
      status:
        alert.severity === "critical"
          ? ("CRITICAL" as const)
          : alert.severity === "high"
            ? ("WARNING" as const)
            : ("NOMINAL" as const),
      value: alert.duplicate_count
        ? `${alert.duplicate_count} duplicates`
        : "Unique",
      time: new Date(alert.detected_at).toLocaleTimeString(),
      desc: alert.title,
    }));
  }, [alerts]);

  const criticalAlerts = threatGridAlerts.filter(
    (a) => a.status === "CRITICAL"
  );

  return (
    <section className="xl:col-span-3 bg-[#080604] p-4 flex flex-col gap-4">
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <span className="text-xs font-display uppercase text-white tracking-widest flex items-center gap-1.5">
            <AlertTriangle className="w-3.5 h-3.5 text-[#ff3333]" />
            Threat Vector Grid
          </span>
          <span className="text-[10px] font-mono bg-[#ff3333]/20 text-[#ff3333] border border-[#ff3333]/40 px-1">
            {criticalAlerts.length} CRIT
          </span>
        </div>

        <div className="space-y-2">
          {threatGridAlerts.map((alert) => (
            <div
              key={alert.id}
              className={`p-3 border ${
                alert.status === "CRITICAL"
                  ? "border-[#ff3333]/40 bg-[#ff3333]/5"
                  : "border-[#ffcc00]/40 bg-[#ffcc00]/5"
              } relative overflow-hidden`}
            >
              <div className="flex justify-between items-start">
                <span className="text-xs font-bold text-white font-mono">
                  {alert.id}
                </span>
                <span
                  className={`text-[9px] px-1 font-mono uppercase ${
                    alert.status === "CRITICAL"
                      ? "bg-[#ff3333] text-black"
                      : "bg-[#ffcc00] text-black"
                  }`}
                >
                  {alert.status}
                </span>
              </div>

              <div className="mt-2 grid grid-cols-2 text-[11px] font-mono border-t border-[#9e5b00]/10 pt-1.5">
                <div>
                  <span className="text-[#9e5b00]">SECTOR:</span>{" "}
                  <span className="text-white">{alert.sector}</span>
                </div>
                <div className="text-right">
                  <span className="text-[#9e5b00]">VAL:</span>{" "}
                  <span className="text-white">{alert.value}</span>
                </div>
              </div>

              <p className="text-[11px] text-[#ff9100]/70 mt-1.5 line-clamp-2 leading-relaxed">
                {alert.desc}
              </p>
            </div>
          ))}
        </div>
      </div>

      <div className="flex-1 border border-[#9e5b00]/20 bg-[#120e0a] p-4 flex flex-col justify-between relative">
        {selectedEntity ? (
          <div className="space-y-4">
            <div className="flex justify-between items-start border-b border-[#9e5b00]/30 pb-2">
              <div>
                <span className="text-[10px] text-[#9e5b00] uppercase block">
                  Inspecting Telemetry Packet
                </span>
                <h4 className="text-sm font-bold text-white font-mono">
                  {selectedEntity.id}
                </h4>
              </div>
              <button
                onClick={clearSelectedEntity}
                className="p-1 hover:bg-[#1c1610] border border-transparent hover:border-[#9e5b00]/30 text-[#9e5b00] hover:text-[#ff9100]"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <div className="space-y-3 text-xs font-mono">
              <div className="p-2 bg-[#080604] border border-[#9e5b00]/10">
                <span className="text-[10px] text-[#9e5b00] uppercase block">
                  TRANSMISSION ORIGIN
                </span>
                <span className="text-white font-bold">
                  {selectedEntity.origin}
                </span>
              </div>

              <div className="p-2 bg-[#080604] border border-[#9e5b00]/10">
                <span className="text-[10px] text-[#9e5b00] uppercase block">
                  TELEMETRY TYPE INDICATOR
                </span>
                <span className="text-[#ff9100]">{selectedEntity.type}</span>
              </div>

              <div className="p-2 bg-[#080604] border border-[#9e5b00]/10">
                <span className="text-[10px] text-[#9e5b00] uppercase block">
                  METRIC VARIANCE DELTA
                </span>
                <span
                  className={
                    selectedEntity.status === "CRITICAL"
                      ? "text-[#ff3333]"
                      : "text-[#00ff66]"
                  }
                >
                  {selectedEntity.delta}
                </span>
              </div>

              <div>
                <span className="text-[10px] text-[#9e5b00] uppercase block mb-1">
                  RAW PACKET STRINGS
                </span>
                <div className="p-2 bg-[#080604] border border-[#9e5b00]/20 text-[11px] text-[#ff9100]/90 leading-normal font-mono h-24 overflow-y-auto">
                  {`{ \n  "packet_id": "${selectedEntity.id}",\n  "timestamp_epoch": "${Date.now()}",\n  "payload_msg": "${selectedEntity.message}",\n  "integrity_hash": "0x89FA${selectedEntity.id}"\n}`}
                </div>
              </div>
            </div>

            <div className="pt-2">
              <button
                onClick={() =>
                  window.alert(
                    `Injecting counter-measure sequence to ${selectedEntity.origin}`
                  )
                }
                className="w-full bg-[#ff9100] hover:bg-[#ff9100]/80 text-black font-display uppercase tracking-widest text-xs py-2 px-3 text-center transition-all duration-150 active:scale-[0.98]"
              >
                Execute Countermeasures
              </button>
            </div>
          </div>
        ) : (
          <div className="h-full flex flex-col items-center justify-center text-center p-4 text-[#9e5b00] my-auto">
            <Database className="w-8 h-8 opacity-30 mb-2 animate-pulse" />
            <p className="text-[11px] uppercase tracking-widest font-mono">
              Select active node or data stream item to intercept telemetry
              payloads.
            </p>
          </div>
        )}
      </div>
    </section>
  );
}
