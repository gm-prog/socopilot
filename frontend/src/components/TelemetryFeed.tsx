import React, { useState, useEffect } from "react";

export const TelemetryFeed = () => {
  const [feed, setFeed] = useState<{id: string, origin: string, message: string, delta: string, ts: string}[]>([]);

  useEffect(() => {
    const msgs = ["Echosounder signal locked", "Pressure equalization cycle finished", "Structural resonance scan clear"];
    const origins = ["NODE-04", "CORE-VALVE", "GRID-A"];
    
    const interval = setInterval(() => {
      const newItem = {
        id: `TX-${Math.floor(1000 + Math.random() * 9000)}`,
        origin: origins[Math.floor(Math.random() * origins.length)],
        message: msgs[Math.floor(Math.random() * msgs.length)],
        delta: `${(Math.random() * 9 - 2).toFixed(2)}%`,
        ts: new Date().toLocaleTimeString()
      };
      setFeed((prev) => [newItem, ...prev.slice(0, 10)]);
    }, 2000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="feed-container">
      {feed.map(item => (
        <div key={item.id} className="feed-item" style={{display: "flex", justifyContent: "space-between", borderBottom: "1px solid var(--line)", padding: "8px 0", fontSize: "12px"}}>
          <span style={{color: "var(--cyan)"}}>{item.ts}</span>
          <span style={{fontWeight: "bold"}}>{item.origin}</span>
          <span>{item.message}</span>
          <span style={{color: parseFloat(item.delta) < 0 ? "#ff4444" : "#00ff00"}}>{item.delta}</span>
        </div>
      ))}
    </div>
  );
};
