import React from 'react';
import { Clock, X } from 'lucide-react';

interface TelemetryRowProps {
  id: string;
  origin: string;
  type: string;
  message: string;
  delta: string;
  timestamp: string;
  status: 'CRITICAL' | 'WARNING' | 'NOMINAL';
  isSelected?: boolean;
  onSelect?: () => void;
  onDeselect?: () => void;
}

const statusColorMap = {
  CRITICAL: { bar: 'bg-data-neg', delta: 'text-data-neg' },
  WARNING: { bar: 'bg-status-warn', delta: 'text-status-warn' },
  NOMINAL: { bar: 'bg-data-pos', delta: 'text-data-pos' },
};

export default function TelemetryRow({
  id,
  origin,
  type,
  message,
  delta,
  timestamp,
  status,
  isSelected = false,
  onSelect,
  onDeselect,
}: TelemetryRowProps) {
  const colors = statusColorMap[status];

  return (
    <div
      onClick={isSelected ? onDeselect : onSelect}
      className={`group border transition-all duration-150 cursor-pointer p-3 bg-phosphor-elevated/40 flex flex-col md:flex-row justify-between items-start md:items-center gap-3 ${
        isSelected
          ? 'border-phosphor-amber bg-phosphor-amber/5'
          : 'border-phosphor-dim/20 hover:border-phosphor-dim/60 hover:bg-phosphor-elevated'
      }`}
    >
      <div className="flex items-start gap-3 flex-1">
        <span
          className={`w-1.5 h-6 block shrink-0 ${colors.bar}`}
        />
        <div className="min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <span className="font-data text-xs text-white font-bold group-hover:text-phosphor-amber whitespace-nowrap">
              {id}
            </span>
            <span className="text-[10px] px-1 bg-phosphor-elevated text-phosphor-dim border border-phosphor-dim/20 font-data whitespace-nowrap">
              {type}
            </span>
            <span className="text-[11px] text-phosphor-dim whitespace-nowrap">{origin}</span>
          </div>
          <p className="text-xs text-phosphor-amber/80 mt-1 font-data tracking-wide break-words">
            {message}
          </p>
        </div>
      </div>

      <div className="flex items-center gap-4 self-end md:self-center text-right font-data text-xs shrink-0">
        <span className={`text-[11px] font-bold ${colors.delta}`}>{delta}</span>
        <span className="text-phosphor-dim text-[11px] flex items-center gap-1 whitespace-nowrap">
          <Clock className="w-3 h-3" />
          {timestamp}
        </span>
      </div>
    </div>
  );
}
