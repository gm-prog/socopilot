import React from 'react';
import { AlertTriangle, Database, X } from 'lucide-react';
import TacticalPanel from '../ui/TacticalPanel';

interface Alert {
  id: string;
  sector: string;
  metric: string;
  status: 'CRITICAL' | 'WARNING' | 'NOMINAL';
  value: string;
  time: string;
  desc: string;
}

interface SelectedEntity {
  id: string;
  origin?: string;
  type?: string;
  message?: string;
  delta?: string;
  status?: 'CRITICAL' | 'WARNING' | 'NOMINAL';
}

interface IncidentConsoleProps {
  alerts: Alert[];
  selectedEntity: SelectedEntity | null;
  onSelectEntity: (entity: SelectedEntity) => void;
  onDeselectEntity: () => void;
}

const statusStyle = {
  CRITICAL: { border: 'border-data-neg/40', bg: 'bg-data-neg/5', label: 'bg-data-neg text-black' },
  WARNING: { border: 'border-status-warn/40', bg: 'bg-status-warn/5', label: 'bg-status-warn text-black' },
  NOMINAL: { border: 'border-data-pos/40', bg: 'bg-data-pos/5', label: 'bg-data-pos text-black' },
};

export default function IncidentConsole({
  alerts,
  selectedEntity,
  onSelectEntity,
  onDeselectEntity,
}: IncidentConsoleProps) {
  return (
    <section className="col-span-3 bg-phosphor-deep p-4 flex flex-col gap-4">
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <span className="text-xs font-display uppercase text-white tracking-widest flex items-center gap-1.5">
            <AlertTriangle className="w-3.5 h-3.5 text-data-neg" />
            Threat Vector Grid
          </span>
          <span className="text-[10px] font-data bg-data-neg/20 text-data-neg border border-data-neg/40 px-1">
            {alerts.filter((a) => a.status === 'CRITICAL').length} CRIT
          </span>
        </div>

        <div className="space-y-2">
          {alerts.map((alert) => {
            const style = statusStyle[alert.status];
            return (
              <div
                key={alert.id}
                className={`p-3 border ${style.border} ${style.bg} relative overflow-hidden`}
              >
                <div className="flex justify-between items-start">
                  <span className="text-xs font-bold text-white font-data">{alert.id}</span>
                  <span
                    className={`text-[9px] px-1 font-data uppercase ${style.label}`}
                  >
                    {alert.status}
                  </span>
                </div>
                <div className="mt-2 grid grid-cols-2 text-[11px] font-data border-t border-phosphor-dim/10 pt-1.5">
                  <div>
                    <span className="text-phosphor-dim">SECTOR:</span>{' '}
                    <span className="text-white">{alert.sector}</span>
                  </div>
                  <div className="text-right">
                    <span className="text-phosphor-dim">VAL:</span>{' '}
                    <span className="text-white">{alert.value}</span>
                  </div>
                </div>
                <p className="text-[11px] text-phosphor-amber/70 mt-1.5 line-clamp-2 leading-relaxed">
                  {alert.desc}
                </p>
              </div>
            );
          })}
        </div>
      </div>

      <div className="flex-1 border border-phosphor-dim/20 bg-phosphor-surface p-4 flex flex-col justify-between relative">
        {selectedEntity ? (
          <div className="space-y-4">
            <div className="flex justify-between items-start border-b border-phosphor-dim/30 pb-2">
              <div>
                <span className="text-[10px] text-phosphor-dim uppercase block">
                  Inspecting Telemetry Packet
                </span>
                <h4 className="text-sm font-bold text-white font-data">
                  {selectedEntity.id}
                </h4>
              </div>
              <button
                onClick={onDeselectEntity}
                className="p-1 hover:bg-phosphor-elevated border border-transparent hover:border-phosphor-dim/30 text-phosphor-dim hover:text-phosphor-amber"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <div className="space-y-3 text-xs font-data">
              <div className="p-2 bg-phosphor-deep border border-phosphor-dim/10">
                <span className="text-[10px] text-phosphor-dim uppercase block">
                  TRANSMISSION ORIGIN
                </span>
                <span className="text-white font-bold">{selectedEntity.origin}</span>
              </div>
              <div className="p-2 bg-phosphor-deep border border-phosphor-dim/10">
                <span className="text-[10px] text-phosphor-dim uppercase block">
                  TELEMETRY TYPE INDICATOR
                </span>
                <span className="text-phosphor-amber">{selectedEntity.type}</span>
              </div>
              <div className="p-2 bg-phosphor-deep border border-phosphor-dim/10">
                <span className="text-[10px] text-phosphor-dim uppercase block">
                  METRIC VARIANCE DELTA
                </span>
                <span
                  className={
                    selectedEntity.status === 'CRITICAL'
                      ? 'text-data-neg'
                      : 'text-data-pos'
                  }
                >
                  {selectedEntity.delta}
                </span>
              </div>
              <div>
                <span className="text-[10px] text-phosphor-dim uppercase block mb-1">
                  RAW PACKET STRINGS
                </span>
                <div className="p-2 bg-phosphor-deep border border-phosphor-dim/20 text-[11px] text-phosphor-amber/90 leading-normal font-data h-24 overflow-y-auto">
                  {`{ \n  "packet_id": "${selectedEntity.id}",\n  "timestamp_epoch": "${Date.now()}",\n  "payload_msg": "${selectedEntity.message || ''}",\n  "integrity_hash": "0x89FA${selectedEntity.id}"\n}`}
                </div>
              </div>
            </div>

            <div className="pt-2">
              <button
                onClick={() =>
                  alert(`Injecting counter-measure sequence to ${selectedEntity.origin}`)
                }
                className="w-full bg-phosphor-amber hover:bg-phosphor-amber/80 text-black font-display uppercase tracking-widest text-xs py-2 px-3 text-center transition-all duration-150 active:scale-[0.98]"
              >
                Execute Countermeasures
              </button>
            </div>
          </div>
        ) : (
          <div className="h-full flex flex-col items-center justify-center text-center p-4 text-phosphor-dim my-auto">
            <Database className="w-8 h-8 opacity-30 mb-2 animate-pulse" />
            <p className="text-[11px] uppercase tracking-widest font-data">
              Select active node or data stream item to intercept telemetry payloads.
            </p>
          </div>
        )}
      </div>
    </section>
  );
}
