import React, { useMemo } from "react";
import { AlertTriangle, Database, X } from "lucide-react";

import { useAlertStore } from "../../store/alertStore";
import type { AlertSummary } from "../../types/alert";

interface IncidentConsoleProps {
  alerts: Array<AlertSummary & { enrichment_summary?: unknown }>;
}

function parseEnrichmentSummary(value: unknown): { kind: "object" | "string" | "empty"; entries?: string[]; text?: string } {
  if (value === null || value === undefined) {
    return { kind: "empty" };
  }

  if (typeof value === "string") {
    const trimmed = value.trim();
    if (!trimmed) {
      return { kind: "empty" };
    }

    try {
      const parsed = JSON.parse(trimmed);
      if (parsed && typeof parsed === "object" && !Array.isArray(parsed)) {
        return { kind: "object", entries: Object.keys(parsed as Record<string, unknown>) };
      }
    } catch {
      // fall back to plain-text rendering below
    }

    return { kind: "string", text: trimmed };
  }

  if (typeof value === "object" && !Array.isArray(value)) {
    return { kind: "object", entries: Object.keys(value as Record<string, unknown>) };
  }

  return { kind: "string", text: String(value) };
}

export default function IncidentConsole({ alerts }: IncidentConsoleProps) {
  const selectedEntity = useAlertStore((state) => state.selectedEntity);
  const setSelectedEntity = useAlertStore((state) => state.setSelectedEntity);

  const selectedAlert = useMemo(
    () => alerts.find((alert) => alert.id === selectedEntity?.id) ?? null,
    [alerts, selectedEntity?.id]
  );

  const enrichment = useMemo(
    () => parseEnrichmentSummary(selectedAlert?.enrichment_summary),
    [selectedAlert]
  );

  return (
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
              onClick={() => setSelectedEntity(null)}
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
              <span className="text-white font-bold">{selectedEntity.origin}</span>
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
                ENRICHMENT SUMMARY
              </span>
              <div className="p-2 bg-[#080604] border border-[#9e5b00]/20 text-[11px] text-[#ff9100]/90 leading-normal font-mono min-h-24 overflow-y-auto">
                {enrichment.kind === "object" && enrichment.entries?.length ? (
                  <ul className="space-y-1">
                    {enrichment.entries.map((entry) => (
                      <li key={entry} className="text-[#ff9100]">
                        {entry}
                      </li>
                    ))}
                  </ul>
                ) : enrichment.kind === "string" && enrichment.text ? (
                  <span>{enrichment.text}</span>
                ) : (
                  <span className="text-[#9e5b00]">No enrichment data available</span>
                )}
              </div>
            </div>
            <div>
              <span className="text-[10px] text-[#9e5b00] uppercase block mb-1">
                RAW PACKET STRINGS
              </span>
              <div className="p-2 bg-[#080604] border border-[#9e5b00]/20 text-[11px] text-[#ff9100]/90 leading-normal font-mono h-24 overflow-y-auto">
                {`{
  "packet_id": "${selectedEntity.id}",
  "timestamp_epoch": "${Date.now()}",
  "payload_msg": "${selectedEntity.message}",
  "integrity_hash": "0x89FA${selectedEntity.id}"
}`}
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
  );
}
