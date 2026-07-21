import React, { useMemo } from "react";
import { useAlertStore, selectActiveFilters } from "../../store/alertStore";
import { mapAlertToFeedItem } from "../../store/feedUtils";
import { Terminal, ShieldAlert, Radio } from "lucide-react";

export default function NavigationRail() {
  const alerts = useAlertStore((state) => state.alerts);
  const activeFilters = useAlertStore(selectActiveFilters);
  const setActiveRail = useAlertStore((state) => state.setActiveRail);

  const feed = useMemo(() => alerts.map(mapAlertToFeedItem), [alerts]);
  const criticalCount = feed.filter((f) => f.status === "CRITICAL").length;
  const nominalCount = feed.filter((f) => f.status === "NOMINAL").length;

  return (
    <nav className="xl:col-span-2 border-r border-[#9e5b00]/30 bg-[#080604] p-4 flex flex-row xl:flex-col justify-between xl:justify-start gap-2">
      <div className="w-full space-y-2">
        <span className="hidden xl:block text-[10px] uppercase tracking-wider text-[#9e5b00] px-2 mb-2 font-display">
          Console Matrices
        </span>

        <button
          onClick={() => setActiveRail("ALL_STATIONS")}
          className={`w-full text-left p-3 flex items-center justify-between transition-all duration-150 relative ${
            activeFilters.activeRail === "ALL_STATIONS"
              ? "bg-[#ff9100]/10 border-l-4 border-[#ff9100] text-white"
              : "hover:bg-[#1c1610] text-[#9e5b00]"
          }`}
        >
          <div className="flex items-center gap-2 text-xs uppercase tracking-wider">
            <Terminal className="w-4 h-4" />
            <span>All Streams</span>
          </div>
          <span className="text-[10px] font-mono bg-[#1c1610] px-1 border border-[#9e5b00]/20">
            {feed.length}
          </span>
        </button>

        <button
          onClick={() => setActiveRail("CRITICAL_ONLY")}
          className={`w-full text-left p-3 flex items-center justify-between transition-all duration-150 relative ${
            activeFilters.activeRail === "CRITICAL_ONLY"
              ? "bg-[#ff3333]/10 border-l-4 border-[#ff3333] text-[#ff3333]"
              : "hover:bg-[#1c1610] text-[#9e5b00]"
          }`}
        >
          <div className="flex items-center gap-2 text-xs uppercase tracking-wider">
            <ShieldAlert className="w-4 h-4" />
            <span>Critical Rails</span>
          </div>
          <span className="text-[10px] font-mono bg-[#ff3333]/20 px-1 border border-[#ff3333]/40 text-[#ff3333]">
            {criticalCount}
          </span>
        </button>

        <button
          onClick={() => setActiveRail("NOMINAL_ONLY")}
          className={`w-full text-left p-3 flex items-center justify-between transition-all duration-150 relative ${
            activeFilters.activeRail === "NOMINAL_ONLY"
              ? "bg-[#00ff66]/10 border-l-4 border-[#00ff66] text-[#00ff66]"
              : "hover:bg-[#1c1610] text-[#9e5b00]"
          }`}
        >
          <div className="flex items-center gap-2 text-xs uppercase tracking-wider">
            <Radio className="w-4 h-4" />
            <span>Nominal Nodes</span>
          </div>
          <span className="text-[10px] font-mono bg-[#00ff66]/20 px-1 border border-[#00ff66]/40 text-[#00ff66]">
            {nominalCount}
          </span>
        </button>
      </div>

      <div className="w-full mt-auto hidden xl:block border-t border-[#9e5b00]/20 pt-4 space-y-3">
        <div className="p-3 bg-[#120e0a] border border-[#9e5b00]/20 text-[11px] text-[#9e5b00]">
          <div className="flex justify-between text-white mb-1">
            <span>STATION GPS</span>
            <span className="animate-pulse">● LIVE</span>
          </div>
          <p>45°12&apos;N 122°33&apos;W</p>
          <p className="mt-1 text-[9px]">DEEP-OCEAN TRENCH GRID 7</p>
        </div>
      </div>
    </nav>
  );
}
