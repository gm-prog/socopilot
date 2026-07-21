import React, { useMemo } from "react";
import { Wifi, WifiOff, AlertTriangle } from "lucide-react";

import MetricsHeader from "../components/dashboard/MetricsHeader";
import NavigationRail from "../components/ui/NavigationRail";
import PrimaryViewport from "../components/dashboard/PrimaryViewport";
import DataDeck from "../components/dashboard/DataDeck";

import { useAlertsStream } from "../hooks/useAlertsStream";
import { useAlertStore } from "../store/alertStore";
import { mapAlertToFeedItem } from "../store/feedUtils";

/**
 * OperationalDashboard (modular composition)
 * Zustand-backed real-time alert architecture — no prop drilling.
 */
export default function OperationalDashboard() {
  // 🟢 Stabilize the stream configuration to prevent infinite re-render loops
  const streamOptions = useMemo(() => ({
    maxQueueSize: 100,
    enabled: true,
  }), []);

  const { isConnected, error, isLoading } = useAlertsStream(streamOptions);

  const alerts = useAlertStore((state) => state.alerts);
  const feedLength = useMemo(
    () => alerts.map(mapAlertToFeedItem).length,
    [alerts]
  );

  return (
    <div className="crt-screen min-h-screen text-[#ff9100] font-data antialiased selection:bg-[#ff9100] selection:text-black">
      <MetricsHeader />

      {error && (
        <div className="bg-[#ff3333]/20 border-b border-[#ff3333]/60 px-6 py-3 flex items-center gap-2 text-[#ff3333] text-sm">
          <AlertTriangle className="w-4 h-4 flex-shrink-0" />
          <span className="font-mono text-xs">{error}</span>
        </div>
      )}

      <main className="grid grid-cols-1 xl:grid-cols-12 min-h-[calc(100vh-73px)] relative z-10">
        <NavigationRail />
        <PrimaryViewport />
        <DataDeck />
      </main>

      <footer className="border-t border-[#9e5b00]/30 bg-[#080604] px-6 py-2 flex flex-col sm:flex-row justify-between items-center text-[10px] tracking-wider uppercase text-[#9e5b00] z-10 relative">
        <div className="flex items-center gap-4">
          <span>OPERATOR_ID: SEC-LEAD-04</span>
          <span className="hidden sm:inline">|</span>
          <span className="flex items-center gap-1">
            {isConnected ? (
              <>
                <Wifi className="w-3 h-3 text-[#00ff66] animate-pulse" />
                STREAM_LIVE
              </>
            ) : (
              <>
                <WifiOff className="w-3 h-3 text-[#ff3333]" />
                STREAM_DISCONNECTED
              </>
            )}
          </span>
          {isLoading && (
            <span className="text-[10px] text-[#ffcc00]">LOADING...</span>
          )}
        </div>

        <div className="mt-1 sm:mt-0 font-mono">
          SYS_TIME: {new Date().toTimeString().split(" ")[0]} PST | ALERTS:{" "}
          {feedLength}
        </div>
      </footer>
    </div>
  );
}