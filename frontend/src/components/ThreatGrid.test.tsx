import React from "react";
import { render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { ThreatGrid } from "./ThreatGrid";
import { useAlertStore } from "../store/alertStore";

vi.mock("../hooks/useAlertsStream", () => ({
  useAlertsStream: () => ({
    isConnected: true,
    error: null,
    isLoading: false,
  }),
}));

describe("ThreatGrid", () => {
  beforeEach(() => {
    useAlertStore.setState({ alerts: [] });
  });

  it("renders alerts from the shared alert store", () => {
    useAlertStore.setState({
      alerts: [
        {
          id: "ALT-42",
          title: "Suspicious beacon activity",
          severity: "critical",
          source: "OPNET",
          duplicate_count: 2,
          detected_at: "2026-07-02T00:00:00Z",
        } as never,
      ],
    });

    render(<ThreatGrid />);

    expect(screen.getByText("ALT-42")).toBeTruthy();
    expect(screen.getByText("Suspicious beacon activity")).toBeTruthy();
  });
});
