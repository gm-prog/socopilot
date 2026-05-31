import React, { useEffect, useMemo, useState } from "react";
import { useAlertsStream } from "../hooks/useAlertsStream";
import {
  useAlertStore,
  selectActiveFilters,
  type FeedItem,
} from "../store/alertStore";
import { mapAlertToFeedItem } from "../store/feedUtils";
import {
  Terminal,
  ShieldAlert,
  Activity,
  Search,
  Sliders,
  Radio,
  Crosshair,
  AlertTriangle,
  X,
  Database,
  Wifi,
  Clock,
} from "lucide-react";

const PhosphorDesignSystem = () => (
  <style>{`
    :root {
      --bg-deep: #080604;
      --bg-surface: #120e0a;
      --bg-elevated: #1c1610;
      --phosphor-amber: #ff9100;
      --phosphor-dim: #9e5b00;
      --phosphor-glow: rgba(255, 145, 0, 0.15);
      --data-pos: #00ff66;
      --data-neg: #ff3333;
      --data-neu: #ff9100;
      --alert-warn: #ffcc00;
      --space-xs: 6px;
      --space-sm: 12px;
      --space-md: 18px;
      --space-lg: 24px;
      --space-xl: 36px;
      --space-2xl: 48px;
      --ease-tactical: cubic-bezier(0.19, 1, 0.22, 1);
    }

    .font-display { font-family: 'Space Grotesk', sans-serif; font-weight: 700; letter-spacing: -0.03em; }
    .font-data { font-family: 'Share Tech Mono', monospace; }
    .crt-screen {
      position: relative;
      background-color: var(--bg-deep);
      overflow: hidden;
    }
    .crt-screen::before {
      content: " ";
      display: block;
      position: absolute;
      top: 0; left: 0; bottom: 0; right: 0;
      background: linear-gradient(rgba(18, 16, 16, 0) 50%, rgba(0, 0, 0, 0.25) 50%), linear-gradient(90deg, rgba(255, 0, 0, 0.06), rgba(0, 255, 0, 0.02), rgba(0, 0, 255, 0.06));
      z-index: 9999;
      background-size: 100% 4px, 6px 100%;
      pointer-events: none;
    }

    ::-webkit-scrollbar { width: 6px; height: 6px; }
    ::-webkit-scrollbar-track { background: var(--bg-deep); }
    ::-webkit-scrollbar-thumb { background: var(--phosphor-dim); border-radius: 0px; }
    ::-webkit-scrollbar-thumb:hover { background: var(--phosphor-amber); }
  `}</style>
);

function filterFeed(
  feed: FeedItem[],
  searchQuery: string,
  activeRail: string
): FeedItem[] {
  const term = searchQuery.toLowerCase();
  return feed.filter((item) => {
    const matchesSearch =
      item.message.toLowerCase().includes(term) ||
      item.origin.toLowerCase().includes(term) ||
      item.id.toLowerCase().includes(term);

    if (activeRail === "ALL_STATIONS") return matchesSearch;
    if (activeRail === "CRITICAL_ONLY")
      return matchesSearch && item.status === "CRITICAL";
    if (activeRail === "NOMINAL_ONLY")
      return matchesSearch && item.status === "NOMINAL";
    return matchesSearch;
  });
}

export default function OperationalDashboard() {
  const alerts = useAlertStore((state) => state.alerts);
  const activeFilters = useAlertStore(selectActiveFilters);
  const selectedEntity = useAlertStore((state) => state.selectedEntity);
  const setSelectedEntity = useAlertStore((state) => state.setSelectedEntity);
  const setSearchQuery = useAlertStore((state) => state.setSearchQuery);
  const setActiveRail = useAlertStore((state) => state.setActiveRail);

  const [systemPulse, setSystemPulse] = useState(true);

  const { isConnected, isLoading, error } = useAlertsStream({
    enabled: true,
    maxQueueSize: 100,
  });

  useEffect(() => {
    const interval = setInterval(() => {
      setSystemPulse((prev) => !prev);
    }, 4000);
    return () => clearInterval(interval);
  }, []);

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

  const criticalAlertCount = useMemo(
    () => alerts.filter((a) => a.severity === "critical").length,
    [alerts]
  );

  const criticalFeedCount = feed.filter((f) => f.status === "CRITICAL").length;
  const nominalFeedCount = feed.filter((f) => f.status === "NOMINAL").length;

  return (
    <div className="crt-screen min-h-screen text-[#ff9100] font-data antialiased selection:bg-[#ff9100] selection:text-black">
      <PhosphorDesignSystem />
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
                {isConnected ? "SYS_ACTIVE" : "SYS_LINKING"}
              </span>
            </div>
            <p className="text-[11px] text-[#9e5b00] tracking-wider uppercase">
              Deep Sea Infrastructure Telemetry Console
            </p>
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-6 text-xs border-l border-[#9e5b00]/30 pl-0 md:pl-6">
          <div className="flex flex-col">
            <span className="text-[#9e5b00] text-[10px] uppercase">
              Acoustic Core Ping
            </span>
            <div className="flex items-center gap-2 mt-0.5">
              <span
                className={`w-2 h-2 rounded-full ${
                  systemPulse ? "bg-[#00ff66]" : "bg-[#9e5b00]"
                } block`}
              ></span>
              <span className="text-white font-bold">12.4 ms</span>
            </div>
          </div>
          <div className="flex flex-col">
            <span className="text-[#9e5b00] text-[10px] uppercase">
              Network Rail Density
            </span>
            <div className="flex items-center gap-2 mt-0.5">
              <Activity className="w-3 h-3 text-[#ff9100]" />
              <span className="text-white font-bold">
                {feed.length.toString().padStart(2, " ")} pkts/s
              </span>
            </div>
          </div>
          <div className="flex flex-col">
            <span className="text-[#9e5b00] text-[10px] uppercase">
              Telemetry Integrity
            </span>
            <div className="flex items-center gap-2 mt-0.5">
              <span className="text-[#00ff66]">99.98%</span>
            </div>
          </div>
        </div>
      </header>

      {error && (
        <div className="bg-[#ff3333]/20 border-b border-[#ff3333]/60 px-6 py-3 flex items-center gap-2 text-[#ff3333] text-sm z-10 relative">
          <AlertTriangle className="w-4 h-4 flex-shrink-0" />
          <span className="font-mono text-xs">{error}</span>
        </div>
      )}

      <main className="grid grid-cols-1 xl:grid-cols-12 min-h-[calc(100vh-73px)] relative z-10">
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
                {criticalFeedCount}
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
                {nominalFeedCount}
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
                <div
                  className="bg-[#ff9100] h-full"
                  style={{ width: "68%" }}
                ></div>
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
                <div
                  className="bg-[#ff9100] h-full"
                  style={{ width: "82%" }}
                ></div>
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
                <div
                  className="bg-[#ff3333] h-full"
                  style={{ width: "12%" }}
                ></div>
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

            {isLoading && feed.length === 0 ? (
              <div className="p-12 text-center border border-dashed border-[#9e5b00]/20 text-[#9e5b00] flex flex-col items-center justify-center gap-2">
                <Sliders className="w-8 h-8 opacity-40 animate-spin" />
                <p className="font-mono text-xs uppercase tracking-widest">
                  Initial signal acquisition in progress.
                </p>
              </div>
            ) : filteredFeed.length === 0 ? (
              <div className="p-12 text-center border border-dashed border-[#9e5b00]/20 text-[#9e5b00] flex flex-col items-center justify-center gap-2">
                <Sliders className="w-8 h-8 opacity-40" />
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
                      className={`w-1.5 h-6 block shrink-0 ${
                        item.status === "CRITICAL"
                          ? "bg-[#ff3333]"
                          : item.status === "WARNING"
                            ? "bg-[#ffcc00]"
                            : "bg-[#00ff66]"
                      }`}
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
                      className={`text-[11px] font-bold ${
                        item.status === "CRITICAL"
                          ? "text-[#ff3333]"
                          : item.status === "WARNING"
                            ? "text-[#ffcc00]"
                            : "text-[#00ff66]"
                      }`}
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

        <section className="xl:col-span-3 bg-[#080604] p-4 flex flex-col gap-4">
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-xs font-display uppercase text-white tracking-widest flex items-center gap-1.5">
                <AlertTriangle className="w-3.5 h-3.5 text-[#ff3333]" />
                Threat Vector Grid
              </span>
              <span className="text-[10px] font-mono bg-[#ff3333]/20 text-[#ff3333] border border-[#ff3333]/40 px-1">
                {criticalAlertCount} CRIT
              </span>
            </div>

            <div className="space-y-2">
              {alerts.map((alert) => (
                <div
                  key={alert.id}
                  className={`p-3 border ${
                    alert.severity === "critical"
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
                        alert.severity === "critical"
                          ? "bg-[#ff3333] text-black"
                          : "bg-[#ffcc00] text-black"
                      }`}
                    >
                      {alert.severity?.toUpperCase() ?? "ALERT"}
                    </span>
                  </div>
                  <div className="mt-2 grid grid-cols-2 text-[11px] font-mono border-t border-[#9e5b00]/10 pt-1.5">
                    <div>
                      <span className="text-[#9e5b00]">SECTOR:</span>{" "}
                      <span className="text-white">{alert.source ?? "N/A"}</span>
                    </div>
                    <div className="text-right">
                      <span className="text-[#9e5b00]">VAL:</span>{" "}
                      <span className="text-white">
                        {alert.duplicate_count ?? "—"}
                      </span>
                    </div>
                  </div>
                  <p className="text-[11px] text-[#ff9100]/70 mt-1.5 line-clamp-2 leading-relaxed">
                    {alert.title ?? "Alert event detected."}
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
        </section>
      </main>

      <footer className="border-t border-[#9e5b00]/30 bg-[#080604] px-6 py-2 flex flex-col sm:flex-row justify-between items-center text-[10px] tracking-wider uppercase text-[#9e5b00] z-10 relative">
        <div className="flex items-center gap-4">
          <span>OPERATOR_ID: SEC-LEAD-04</span>
          <span className="hidden sm:inline">|</span>
          <span className="flex items-center gap-1">
            <Wifi className="w-3 h-3 text-[#00ff66]" /> CRYPTO-ENC LINK STABLE
          </span>
        </div>
        <div className="mt-1 sm:mt-0 font-mono">
          SYS_TIME: {new Date().toTimeString().split(" ")[0]} PST
        </div>
      </footer>
    </div>
  );
}
