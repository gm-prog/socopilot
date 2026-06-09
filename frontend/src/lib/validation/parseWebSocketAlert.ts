import { WebSocketAlertPayloadSchema } from "../../schemas/alert";
import type { AlertSummary } from "../types/alert";
import { reportValidationError } from "./reportValidationError";
import { useValidationStore } from "../../store/validationStore";

export function parseWebSocketAlertFrame(raw: string): AlertSummary | null {
  let json: unknown;
  try {
    json = JSON.parse(raw);
  } catch {
    useValidationStore.getState().incrementDroppedPackets();
    reportValidationError({
      source: "websocket",
      message: "Malformed JSON in WebSocket frame",
      rawPreview: raw.slice(0, 200),
    });
    return null;
  }

  const frameResult = WebSocketAlertPayloadSchema.safeParse(json);
  if (!frameResult.success) {
    useValidationStore.getState().incrementDroppedPackets();
    reportValidationError({
      source: "websocket",
      message: "WebSocket frame failed schema validation",
      issues: frameResult.error.issues,
      rawPreview: raw.slice(0, 200),
    });
    return null;
  }

  const payload = frameResult.data;

  if ("type" in payload && payload.type === "NEW_ALERT") {
    return payload.data;
  }

  return payload;
}
