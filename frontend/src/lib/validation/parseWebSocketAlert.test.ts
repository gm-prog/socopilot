import { describe, expect, it, vi, beforeEach } from "vitest";

import { parseWebSocketAlertFrame } from "./parseWebSocketAlert";
import { useValidationStore } from "../../store/validationStore";

const VALID_ALERT = {
  id: "550e8400-e29b-41d4-a716-446655440000",
  title: "Test Alert",
  severity: "critical",
  status: "open",
  lifecycle_state: "new",
  source: "crowdstrike",
  detected_at: "2024-05-28T21:43:12Z",
  ingested_at: "2024-05-28T21:43:13Z",
  last_seen_at: "2024-05-28T21:43:13Z",
  duplicate_count: 1,
  fingerprint: "abc123",
  time_bucket: "2024-05-28T21:00:00Z",
  assigned_to: null,
  tags: [],
};

describe("parseWebSocketAlertFrame", () => {
  beforeEach(() => {
    useValidationStore.getState().clearErrors();
    vi.spyOn(console, "warn").mockImplementation(() => {});
  });

  it("parses NEW_ALERT envelope", () => {
    const frame = JSON.stringify({
      type: "NEW_ALERT",
      tenant_id: "tenant-1",
      data: VALID_ALERT,
    });
    const result = parseWebSocketAlertFrame(frame);
    expect(result?.id).toBe(VALID_ALERT.id);
    expect(useValidationStore.getState().droppedPacketCount).toBe(0);
  });

  it("parses bare alert payload", () => {
    const result = parseWebSocketAlertFrame(JSON.stringify(VALID_ALERT));
    expect(result?.title).toBe("Test Alert");
  });

  it("drops invalid packets and increments counter", () => {
    const result = parseWebSocketAlertFrame(JSON.stringify({ foo: "bar" }));
    expect(result).toBeNull();
    expect(useValidationStore.getState().droppedPacketCount).toBe(1);
  });

  it("drops malformed JSON", () => {
    const result = parseWebSocketAlertFrame("{not-json");
    expect(result).toBeNull();
    expect(useValidationStore.getState().droppedPacketCount).toBe(1);
  });
});
