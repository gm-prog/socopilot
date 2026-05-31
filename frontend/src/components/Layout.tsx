import { Link, useLocation } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import type { ReactNode } from "react";

interface LayoutProps {
  children: ReactNode;
}

const nav = [
  { to: "/", label: "Dashboard", icon: "⌘" },
  { to: "/alerts", label: "Alerts", icon: "⚠" },
  { to: "/search", label: "Search", icon: "🔍" },
  { to: "/status", label: "Status", icon: "⛭" },
  { to: "/ops", label: "Ops", icon: "⚙" },
];

export default function Layout({ children }: LayoutProps) {
  const location = useLocation();
  const { isAuthenticated } = useAuth();

  return (
    <div className="min-h-screen bg-heritage-bg text-heritage-text">
      <div className="grid min-h-screen grid-cols-[80px_1fr]">
        <aside className="bg-heritage-ink border-r border-heritage-goldBorder flex flex-col items-center py-6 gap-8">
          <div className="h-14 w-14 rounded-full border border-heritage-goldBorder bg-heritage-surface/90 flex items-center justify-center text-heritage-gold font-serif text-base tracking-[0.35em]">
            HI
          </div>

          <nav className="flex flex-col gap-4">
            {nav.map((item) => {
              const active = location.pathname === item.to;
              return (
                <Link
                  key={item.to}
                  to={item.to}
                  title={item.label}
                  className="relative group"
                >
                  <span className={`text-2xl transition duration-400 ease-premium ${
                    active ? "text-heritage-gold" : "text-heritage-muted group-hover:text-heritage-text"
                  }`}>
                    {item.icon}
                  </span>
                  {active && (
                    <div className="absolute left-0 top-1/2 -translate-y-1/2 -translate-x-1 w-0.5 h-6 rounded-full bg-heritage-gold" />
                  )}
                </Link>
              );
            })}
          </nav>

          <div className="mt-auto">
            <span
              className={`text-[10px] font-semibold uppercase tracking-[0.35em] px-2 py-1 rounded-full border ${
                isAuthenticated
                  ? "border-heritage-emerald/30 bg-heritage-emerald/10 text-heritage-emerald"
                  : "border-heritage-burgundy/30 bg-heritage-burgundy/10 text-heritage-burgundy"
              }`}>
              {isAuthenticated ? "secure" : "guest"}
            </span>
          </div>
        </aside>

        <div className="flex flex-col overflow-hidden">
          <header className="border-b border-heritage-goldBorder bg-heritage-surface/85 backdrop-blur px-8 py-6 flex items-center justify-between gap-6">
            <div>
              <p className="text-[11px] uppercase tracking-[0.4em] text-heritage-muted">
                Heritage Intelligence Console
              </p>
              <h1 className="mt-2 text-3xl font-serif tracking-[0.05em]">SOCoPilot</h1>
            </div>
            <div
              className={`rounded-full border px-3 py-1 text-[11px] uppercase tracking-[0.3em] ${
                isAuthenticated
                  ? "border-heritage-emerald bg-heritage-emerald/10 text-heritage-emerald"
                  : "border-heritage-burgundy bg-heritage-burgundy/10 text-heritage-burgundy"
              }`}>
              {isAuthenticated ? "Authenticated" : "Not logged in"}
            </div>
          </header>

          <main className="flex-1 overflow-auto px-8 py-10">{children}</main>

          <footer className="border-t border-heritage-goldBorder px-8 py-4 text-center text-xs uppercase tracking-[0.28em] text-heritage-muted">
            SOCoPilot v0.2.0 — Heritage Console
          </footer>
        </div>
      </div>
    </div>
  );
}
