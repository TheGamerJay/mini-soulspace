/**
 * Typed API client for the Mini SoulSpace backend.
 *
 * The base URL is provided at build time via NEXT_PUBLIC_API_URL and defaults
 * to the local FastAPI server.
 */

export const API_URL =
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export interface HealthResponse {
  status: string;
}

/** Call the backend health endpoint. */
export async function getHealth(): Promise<HealthResponse> {
  const res = await fetch(`${API_URL}/health`, { cache: "no-store" });
  if (!res.ok) {
    throw new Error(`Health check failed: ${res.status}`);
  }
  return res.json();
}
