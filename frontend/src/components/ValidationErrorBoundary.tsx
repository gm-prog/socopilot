import React, { Component, type ErrorInfo, type ReactNode } from "react";

import { useValidationStore } from "../store/validationStore";

interface Props {
  children: ReactNode;
}

interface State {
  hasReactError: boolean;
  reactError: Error | null;
}

/**
 * Catches React render errors and surfaces schema validation drops
 * from the validation store (WebSocket / API contract violations).
 */
export class ValidationErrorBoundary extends Component<Props, State> {
  state: State = { hasReactError: false, reactError: null };

  static getDerivedStateFromError(error: Error): Partial<State> {
    return { hasReactError: true, reactError: error };
  }

  componentDidCatch(error: Error, info: ErrorInfo): void {
    if (import.meta.env.DEV) {
      console.error("[ValidationErrorBoundary]", error, info.componentStack);
    }
  }

  render() {
    if (this.state.hasReactError) {
      return (
        <div className="min-h-screen bg-[#080604] text-[#ff3333] p-8 font-mono">
          <h1 className="text-lg uppercase tracking-widest mb-4">
            Console Fault — Render Error
          </h1>
          <p className="text-sm text-[#ff9100]/80 mb-6">
            {this.state.reactError?.message ?? "Unknown error"}
          </p>
          <button
            type="button"
            onClick={() => window.location.reload()}
            className="border border-[#ff9100] px-4 py-2 text-[#ff9100] text-xs uppercase tracking-wider hover:bg-[#ff9100]/10"
          >
            Reload Console
          </button>
        </div>
      );
    }

    return (
      <>
        <ValidationTelemetryBanner />
        {this.props.children}
      </>
    );
  }
}

function ValidationTelemetryBanner() {
  const errors = useValidationStore((s) => s.errors);
  const droppedCount = useValidationStore((s) => s.droppedPacketCount);
  const clearErrors = useValidationStore((s) => s.clearErrors);

  const latest = errors[0];
  if (!latest && droppedCount === 0) return null;

  return (
    <div
      className="relative z-[9998] border-b border-[#ff3333]/40 bg-[#1c0808]/95 px-4 py-2 text-[11px] font-mono text-[#ff9100]"
      role="alert"
    >
      <div className="flex flex-wrap items-center justify-between gap-2 max-w-screen-2xl mx-auto">
        <div className="flex flex-wrap items-center gap-3">
          <span className="text-[#ff3333] uppercase tracking-wider font-bold">
            Schema Guard
          </span>
          {droppedCount > 0 && (
            <span className="text-[#ffcc00]">
              {droppedCount} packet{droppedCount === 1 ? "" : "s"} dropped
            </span>
          )}
          {latest && (
            <span className="text-[#9e5b00] truncate max-w-xl">
              [{latest.source}] {latest.message}
            </span>
          )}
        </div>
        <button
          type="button"
          onClick={clearErrors}
          className="text-[#9e5b00] hover:text-[#ff9100] uppercase tracking-wider shrink-0"
        >
          Dismiss
        </button>
      </div>
    </div>
  );
}

export default ValidationErrorBoundary;
