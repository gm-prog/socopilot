import type { ZodIssue } from "zod";

import { useValidationStore } from "../../store/validationStore";

export interface ValidationReport {
  source: "websocket" | "api" | "unknown";
  message: string;
  issues?: ZodIssue[];
  rawPreview?: string;
}

const MAX_STORED_ERRORS = 25;

export function reportValidationError(report: ValidationReport): void {
  const entry = {
    id: `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`,
    timestamp: new Date().toISOString(),
    ...report,
  };

  if (import.meta.env.DEV) {
    console.warn("[SOCopilot] Schema validation failed:", entry);
  }

  useValidationStore.getState().pushError(entry);
}

export function formatZodIssues(issues: ZodIssue[]): string {
  return issues
    .slice(0, 3)
    .map((issue) => `${issue.path.join(".") || "root"}: ${issue.message}`)
    .join("; ");
}
