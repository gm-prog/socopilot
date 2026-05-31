import React, { useState, useMemo } from 'react';
import { Wifi, WifiOff, AlertTriangle } from 'lucide-react';

import MetricsHeader from '../components/dashboard/MetricsHeader';
import NavigationRail from '../components/ui/NavigationRail';
import PrimaryViewport from '../components/dashboard/PrimaryViewport';
import DataDeck from '../components/dashboard/DataDeck';

import { useAlertsStream } from '../hooks/useAlertsStream';
import { useAlertStore } from '../store/useAlertStore';

import type { AlertSummary } from '../types/alert';

interface FeedItem {
  id: string;
  type: string;
  origin: string;
  message: string;
  delta: string;
  status: 'CRITICAL' | 'WARNING' | 'NOMINAL';
  timestamp: string;
}

// Helper: Convert AlertSummary to FeedItem
const alertToFeedItem = (alert: AlertSummary): FeedItem => {
  const status =
    alert.severity === 'critical'
      ? 'CRITICAL'
      : alert.severity === 'high'
      ? 'WARNING'
      : 'NOMINAL';

  return {
    id: alert.id,
    type: 'ALERT_INGRESS',
    origin: alert.source || 'UNKNOWN',
    message: alert.title,
    delta: alert.duplicate_count
      ? `+${alert.duplicate_count} dup`
      : '0',
    status,
    timestamp: new Date(alert.detected_at).toLocaleTimeString(
      'en-US',
      {
        hour12: false,
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
      }
    ),
  };
};

/**
 * OperationalDashboard
 * Main retro-operational command console
 * Zustand-backed real-time alert architecture
 */
export default function OperationalDashboard() {
  /**
   * Stream hook now ONLY manages:
   * - websocket lifecycle
   * - reconnect logic
   * - auth refresh
   * - ingestion pipeline
   */
  const {
    isConnected,
    error,
    isLoading,
  } = useAlertsStream({
    maxQueueSize: 100,
    enabled: true,
  });

  /**
   * Global centralized alert state
   */
  const streamedAlerts = useAlertStore(
    (state) => state.alerts
  );

  const [searchTerm, setSearchTerm] = useState('');
  const [selectedEntity, setSelectedEntity] =
    useState<FeedItem | null>(null);

  const [activeRail, setActiveRail] =
    useState('ALL_STATIONS');

  /**
   * Feed transformation layer
   */
  const feed = useMemo(() => {
    return streamedAlerts.map(alertToFeedItem);
  }, [streamedAlerts]);

  /**
   * Legacy compatibility adapter
   * Used by DataDeck
   */
  const alerts = useMemo(() => {
    return streamedAlerts.slice(0, 5).map((alert) => ({
      id: alert.id,
      sector: `SEC-${
        alert.source?.substring(0, 2).toUpperCase() || 'XX'
      }`,
      metric: alert.source || 'Unknown Source',
      status:
        alert.severity === 'critical'
          ? 'CRITICAL'
          : alert.severity === 'high'
          ? 'WARNING'
          : 'NOMINAL' as const,
      value: alert.duplicate_count
        ? `${alert.duplicate_count} duplicates`
        : 'Unique',
      time: new Date(
        alert.detected_at
      ).toLocaleTimeString(),
      desc: alert.title,
    }));
  }, [streamedAlerts]);

  const criticalCount = feed.filter(
    (f) => f.status === 'CRITICAL'
  ).length;

  const nominalCount = feed.filter(
    (f) => f.status === 'NOMINAL'
  ).length;

  return (
    <div className="crt-screen min-h-screen text-[#ff9100] font-data antialiased selection:bg-[#ff9100] selection:text-black">
      <MetricsHeader />

      {/* Stream Status Alert Banner */}
      {error && (
        <div className="bg-[#ff3333]/20 border-b border-[#ff3333]/60 px-6 py-3 flex items-center gap-2 text-[#ff3333] text-sm">
          <AlertTriangle className="w-4 h-4 flex-shrink-0" />
          <span className="font-mono text-xs">
            {error}
          </span>
        </div>
      )}

      {/* CORE OPERATIONAL ZONED COMPOSITION */}
      <main className="grid grid-cols-1 xl:grid-cols-12 min-h-[calc(100vh-73px)] relative z-10">
        <NavigationRail
          activeRail={activeRail}
          feedLength={feed.length}
          criticalCount={criticalCount}
          nominalCount={nominalCount}
          onRailChange={setActiveRail}
        />

        <PrimaryViewport
          feed={feed}
          searchTerm={searchTerm}
          onSearchChange={setSearchTerm}
          activeRail={activeRail}
          selectedEntity={selectedEntity}
          onEntitySelect={setSelectedEntity}
        />

        <DataDeck
          alerts={alerts as any}
          selectedEntity={selectedEntity}
          onEntityClose={() =>
            setSelectedEntity(null)
          }
        />
      </main>

      {/* CORE STATUS FOOTER RAIL */}
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
            <span className="text-[10px] text-[#ffcc00]">
              LOADING...
            </span>
          )}
        </div>

        <div className="mt-1 sm:mt-0 font-mono">
          SYS_TIME:{' '}
          {new Date()
            .toTimeString()
            .split(' ')[0]}{' '}
          PST | ALERTS: {feed.length}
        </div>
      </footer>
    </div>
  );
}