/**
 * Typed API client for the Mini SoulSpace backend.
 *
 * In the unified deployment the frontend and backend share one origin, so the
 * base URL defaults to empty (same-origin) and all endpoints live under `/api`.
 * Set NEXT_PUBLIC_API_URL at build time only when pointing at a separate host.
 */

export const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "";
export const API_URL = `${API_BASE}/api`;

export interface HealthResponse {
  status: string;
}

/** Call the backend liveness endpoint. */
export async function getHealth(): Promise<HealthResponse> {
  const res = await fetch(`${API_URL}/health`, { cache: "no-store" });
  if (!res.ok) {
    throw new Error(`Health check failed: ${res.status}`);
  }
  return res.json();
}
