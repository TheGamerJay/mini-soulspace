"use client";

import { useRouter } from "next/navigation";
import { useEffect, type ReactNode } from "react";
import { useAuthStore } from "@/stores/authStore";

/**
 * Client-side route guard. In a static-export SPA there is no server middleware,
 * so protected pages verify the session via /api/auth/me and redirect guests to
 * /login. The API independently enforces auth on every protected endpoint.
 */
export function AuthGuard({ children }: { children: ReactNode }) {
  const router = useRouter();
  const status = useAuthStore((s) => s.status);
  const hydrate = useAuthStore((s) => s.hydrate);

  useEffect(() => {
    if (status === "idle") {
      hydrate();
    }
  }, [status, hydrate]);

  useEffect(() => {
    if (status === "unauthenticated") {
      router.replace("/login");
    }
  }, [status, router]);

  if (status !== "authenticated") {
    return (
      <div className="flex min-h-screen items-center justify-center text-soul-muted">
        Loading…
      </div>
    );
  }

  return <>{children}</>;
}
