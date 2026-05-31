import React, { useState, useEffect } from "react";

export const ThreatGrid = () => {
  const [alerts, setAlerts] = useState<{id: string, status: string, sector: string}[]>([]);

  useEffect(() => {
    const interval = setInterval(() => {
      const statuses = ["NOMINAL", "WARNING", "CRITICAL"];
      const newAlert = {
        id: `ALT-${Math.floor(Math.random() * 900)}`,
        status: statuses[Math.floor(Math.random() * statuses.length)],
        sector: `SEC-0${Math.floor(Math.random() * 9)}`
      };
      setAlerts((prev) => [newAlert, ...prev].slice(0, 4));
    }, 5000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="alerts-section">
      {alerts.map((alert) => (
        <div key={alert.id} className={`alert-card ${alert.status.toLowerCase()}`}>
          <span>{alert.sector}</span> | <span>{alert.status}</span>
        </div>
      ))}
    </div>
  );
};
