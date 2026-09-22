import { render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it } from "vitest";

import IncidentConsole from "./IncidentConsole";
import { useAlertStore } from "../../store/alertStore";

describe("IncidentConsole", () => {
  beforeEach(() => {
    useAlertStore.setState({ selectedEntity: null, alerts: [] });
  });

  it("shows a fallback message when enrichment data is empty", () => {
    useAlertStore.setState({
      selectedEntity: {
        id: "alert-1",
        type: "ALERT",
        origin: "source-a",
        message: "test",
        delta: "0",
        status: "CRITICAL",
        timestamp: "12:00:00",
      },
    });

    render(<IncidentConsole alerts={[{ id: "alert-1", enrichment_summary: "" }]} />);

    expect(screen.getByText("No enrichment data available")).toBeTruthy();
  });

  it("renders parsed enrichment keys from a JSON string", () => {
    useAlertStore.setState({
      selectedEntity: {
        id: "alert-2",
        type: "ALERT",
        origin: "source-b",
        message: "test",
        delta: "1",
        status: "WARNING",
        timestamp: "12:01:00",
      },
    });

    render(
      <IncidentConsole
        alerts={[{ id: "alert-2", enrichment_summary: '{"foo":"bar","baz":2}' }]}
      />
    );

    expect(screen.getByText("foo")).toBeTruthy();
    expect(screen.getByText("baz")).toBeTruthy();
  });
});
