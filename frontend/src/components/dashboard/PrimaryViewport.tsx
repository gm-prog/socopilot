import React, { useMemo } from "react";
import { Search, Sliders, X, Clock } from "lucide-react";
import { useAlertStore, selectActiveFilters } from "../../store/alertStore";
import { mapAlertToFeedItem } from "../../store/feedUtils";

function filterFeed(
  feed: ReturnType<typeof mapAlertToFeedItem>[],
  searchQuery: string,
  activeRail: string
) {
  return feed.filter((item) => {
    const matchesSearch =
      item.message.toLowerCase().includes(searchQuery.toLowerCase()) ||
      item.origin.toLowerCase().includes(searchQuery.toLowerCase()) ||
      item.id.toLowerCase().includes(searchQuery.toLowerCase());
    if (activeRail === "ALL_STATIONS") return matchesSearch;
    if (activeRail === "CRITICAL_ONLY")
      return matchesSearch && item.status === "CRITICAL";
    if (activeRail === "NOMINAL_ONLY")
      return matchesSearch && item.status === "NOMINAL";
    return matchesSearch;
  });
}

export default function PrimaryViewport() {
  const alerts = useAlertStore((state) => state.alerts);
  const activeFilters = useAlertStore(selectActiveFilters);
  const selectedEntity = useAlertStore((state) => state.selectedEntity);
  const setSearchQuery = useAlertStore((state) => state.setSearchQuery);
  const setSelectedEntity = useAlertStore((state) => state.setSelectedEntity);

  const feed = useMemo(() => alerts.map(mapAlertToFeedItem), [alerts]);

  const filteredFeed = useMemo(
    () =>
      filterFeed(
        feed,
        activeFilters.searchQuery,
        activeFilters.activeRail
      ),
    [feed, activeFilters.searchQuery, activeFilters.activeRail]
  );

  const getStatusColor = (status: string): string => {
    switch (status) {
      case "CRITICAL":
        return "bg-[#ff3333]";
      case "WARNING":
        return "bg-[#ffcc00]";
      default:
        return "bg-[#00ff66]";
    }
  };

  const getStatusTextColor = (status: string): string => {
    switch (status) {
      case "CRITICAL":
        return "text-[#ff3333]";
      case "WARNING":
        return "text-[#ffcc00]";
      default:
        return "text-[#00ff66]";
    }
  };

  return (
    <section className="xl:col-span-7 bg-[#120e0a] flex flex-col border-r border-[#9e5b00]/30">
      <div className="grid grid-cols-2 sm:grid-cols-4 border-b border-[#9e5b00]/30 bg-[#080604]">
        <div className="p-4 border-r border-[#9e5b00]/20">
          <span className="text-[10px] text-[#9e5b00] tracking-wider uppercase block">
            Hydrostatic Load
          </span>
          <div className="text-xl font-bold text-white tracking-tight mt-1 font-mono">
            104.22 <span className="text-xs text-[#ff9100]">BAR</span>
          </div>
          <div className="w-full bg-[#1c1610] h-1 mt-2 overflow-hidden relative">
            <div className="bg-[#ff9100] h-full" style={{ width: "68%" }}></div>
          </div>
        </div>
        <div className="p-4 border-r border-[#9e5b00]/20">
          <span className="text-[10px] text-[#9e5b00] tracking-wider uppercase block">
            Acoustic Array
          </span>
          <div className="text-xl font-bold text-[#00ff66] tracking-tight mt-1 font-mono">
            STABLE{" "}
            <span className="text-xs text-[#9e5b00] font-normal">
              Grid Delta
            </span>
          </div>
          <div className="w-full bg-[#1c1610] h-1 mt-2 overflow-hidden relative">
            <div className="bg-[#00ff66] h-full w-full animate-pulse"></div>
          </div>
        </div>
        <div className="p-4 border-r border-[#9e5b00]/20">
          <span className="text-[10px] text-[#9e5b00] tracking-wider uppercase block">
            Lithium Reserves
          </span>
          <div className="text-xl font-bold text-white tracking-tight mt-1 font-mono">
            82.14 <span className="text-xs text-[#ff9100]">%</span>
          </div>
          <div className="w-full bg-[#1c1610] h-1 mt-2 overflow-hidden relative">
            <div className="bg-[#ff9100] h-full" style={{ width: "82%" }}></div>
          </div>
        </div>
        <div className="p-4">
          <span className="text-[10px] text-[#9e5b00] tracking-wider uppercase block">
            Seismic Activity
          </span>
          <div className="text-xl font-bold text-[#ff3333] tracking-tight mt-1 font-mono">
            0.04 <span className="text-xs text-[#ff3333]">V_R</span>
          </div>
          <div className="w-full bg-[#1c1610] h-1 mt-2 overflow-hidden relative">
            <div className="bg-[#ff3333] h-full" style={{ width: "12%" }}></div>
          </div>
        </div>
      </div>

      <div className="p-4 border-b border-[#9e5b00]/20 bg-[#120e0a] flex items-center gap-3">
        <Search className="w-4 h-4 text-[#9e5b00] shrink-0" />
        <input
          type="text"
          placeholder="COMMAND INPUT: FILTER MATRIX TRANSIENTS BY ID, SIGNATURE, OR ORIGIN..."
          value={activeFilters.searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="w-full bg-transparent text-sm text-[#ff9100] placeholder-[#9e5b00]/50 border-none outline-none focus:ring-0 font-mono tracking-wider"
        />
        {activeFilters.searchQuery && (
          <button
            onClick={() => setSearchQuery("")}
            className="text-[#9e5b00] hover:text-[#ff9100]"
          >
            <X className="w-4 h-4" />
          </button>
        )}
      </div>

      <div className="flex-1 overflow-y-auto p-4 space-y-2">
        <div className="flex items-center justify-between text-[11px] text-[#9e5b00] uppercase tracking-wider pb-2 border-b border-[#9e5b00]/10">
          <span>Live Telemetry Broadcast Pipeline</span>
          <span>Filter: {activeFilters.activeRail}</span>
        </div>

        {filteredFeed.length === 0 ? (
          <div className="p-12 text-center border border-dashed border-[#9e5b00]/20 text-[#9e5b00] flex flex-col items-center justify-center gap-2">
            <Sliders className="w-8 h-8 opacity-40 animate-spin" />
            <p className="font-mono text-xs uppercase tracking-widest">
              No signals intercepted matching current parameters.
            </p>
          </div>
        ) : (
          filteredFeed.map((item) => (
            <div
              key={item.id}
              onClick={() => setSelectedEntity(item)}
              className={`group border transition-all duration-150 cursor-pointer p-3 bg-[#1c1610]/40 flex flex-col md:flex-row justify-between items-start md:items-center gap-3 ${
                selectedEntity?.id === item.id
                  ? "border-[#ff9100] bg-[#ff9100]/5"
                  : "border-[#9e5b00]/20 hover:border-[#9e5b00]/60 hover:bg-[#1c1610]"
              }`}
            >
              <div className="flex items-start gap-3">
                <span
                  className={`w-1.5 h-6 block shrink-0 ${getStatusColor(
                    item.status
                  )}`}
                />

                <div>
                  <div className="flex items-center gap-2">
                    <span className="font-mono text-xs text-white font-bold group-hover:text-[#ff9100]">
                      {item.id}
                    </span>
                    <span className="text-[10px] px-1 bg-[#1c1610] text-[#9e5b00] border border-[#9e5b00]/20 font-mono">
                      {item.type}
                    </span>
                    <span className="text-[11px] text-[#9e5b00]">
                      {item.origin}
                    </span>
                  </div>
                  <p className="text-xs text-[#ff9100]/80 mt-1 font-mono tracking-wide">
                    {item.message}
                  </p>
                </div>
              </div>

              <div className="flex items-center gap-4 self-end md:self-center text-right font-mono text-xs">
                <span
                  className={`text-[11px] font-bold ${getStatusTextColor(
                    item.status
                  )}`}
                >
                  {item.delta}
                </span>
                <span className="text-[#9e5b00] text-[11px] flex items-center gap-1">
                  <Clock className="w-3 h-3" />
                  {item.timestamp}
                </span>
              </div>
            </div>
          ))
        )}
      </div>
    </section>
  );
}
