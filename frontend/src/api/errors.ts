import type { ZodError } from "zod";

export class ApiError extends Error {
  readonly status: number;
  readonly path: string;
  readonly validationError?: ZodError;

  constructor(
    message: string,
    status: number,
    path: string,
    validationError?: ZodError
  ) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.path = path;
    this.validationError = validationError;
  }
}

export function isApiError(error: unknown): error is ApiError {
  return error instanceof ApiError;
}
