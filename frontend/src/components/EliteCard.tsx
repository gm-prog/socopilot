import type { ReactNode } from "react";

interface EliteCardProps {
  children: ReactNode;
  className?: string;
}

export function EliteCard({ children, className = "" }: EliteCardProps) {
  return (
    <div
      className={`rounded-3xl border border-[rgba(198,161,91,0.16)] bg-heritage-surface/95 px-5 py-5 shadow-[0_24px_80px_-40px_rgba(0,0,0,0.6)] transition duration-300 ${className}`}
    >
      {children}
    </div>
  );
}
