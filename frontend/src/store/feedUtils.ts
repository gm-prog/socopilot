import type { AlertSummary } from "../types/alert";
import type { FeedItem, FeedStatus } from "./alertStore";

export function mapAlertToFeedItem(alert: AlertSummary): FeedItem {
  const status: FeedStatus =
    alert.severity === "critical"
      ? "CRITICAL"
      : alert.severity === "high" || alert.severity === "medium"
        ? "WARNING"
        : "NOMINAL";

  return {
    id: alert.id,
    type: "ALERT",
    origin: alert.source || "UNKNOWN",
    message: alert.title || "Suspicious telemetry event",
    delta: alert.duplicate_count ? `${alert.duplicate_count} dup` : "0",
    status,
    timestamp: alert.detected_at
      ? new Date(alert.detected_at).toTimeString().split(" ")[0]
      : new Date().toTimeString().split(" ")[0],
  };
}
