import React from "react";

export const Dashboard = () => {
  return (
    <div className="app">
      <header>
        <div className="brand-name">NEPTUNE-VII</div>
      </header>
      <main className="main">
        <nav className="left-nav">STREAMS</nav>
        <section className="center">TELEMETRY FEED</section>
        <aside className="right-panel">THREAT GRID</aside>
      </main>
    </div>
  );
};
