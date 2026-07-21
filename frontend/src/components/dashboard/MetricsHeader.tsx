import React from 'react';
import { Activity, Crosshair } from 'lucide-react';

export default function MetricsHeader() {
  return (
    <header className="border-b border-[#9e5b00]/30 bg-[#120e0a] px-6 py-4 flex flex-col md:flex-row justify-between items-start md:items-center gap-4 z-10 relative">
      <div className="flex items-center gap-4">
        <div className="bg-[#ff9100]/10 p-2 border border-[#ff9100] animate-pulse">
          <Crosshair className="w-6 h-6 text-[#ff9100]" />
        </div>
        <div>
          <div className="flex items-center gap-2">
            <h1 className="font-display text-xl uppercase tracking-widest text-[#ff9100]">
              NEPTUNE-IV
            </h1>
            <span className="text-[10px] bg-[#ff9100]/20 border border-[#ff9100] px-1 text-xs">
              SYS_ACTIVE
            </span>
          </div>
          <p className="text-[11px] text-[#9e5b00] tracking-wider uppercase">
            Deep Sea Infrastructure Telemetry Console
          </p>
        </div>
      </div>

      {/* Global Operational Metrics */}
      <div className="flex flex-wrap items-center gap-6 text-xs border-l border-[#9e5b00]/30 pl-0 md:pl-6">
        <div className="flex flex-col">
          <span className="text-[#9e5b00] text-[10px] uppercase">Acoustic Core Ping</span>
          <div className="flex items-center gap-2 mt-0.5">
            <span className="w-2 h-2 rounded-full bg-[#00ff66] block"></span>
            <span className="text-white font-bold">12.4 ms</span>
          </div>
        </div>
        <div className="flex flex-col">
          <span className="text-[#9e5b00] text-[10px] uppercase">Network Rail Density</span>
          <div className="flex items-center gap-2 mt-0.5">
            <Activity className="w-3 h-3 text-[#ff9100]" />
            <span className="text-white font-bold">894 pkts/s</span>
          </div>
        </div>
        <div className="flex flex-col">
          <span className="text-[#9e5b00] text-[10px] uppercase">Telemetry Integrity</span>
          <div className="flex items-center gap-2 mt-0.5">
            <span className="text-[#00ff66]">99.98%</span>
          </div>
        </div>
      </div>
    </header>
  );
}
