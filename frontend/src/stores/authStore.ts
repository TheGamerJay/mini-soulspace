"use client";

import { create } from "zustand";
import { authApi, ApiError } from "@/lib/api";
import type { RegisterPayload, User, UserPreferences } from "@/lib/types";

type Status = "idle" | "loading" | "authenticated" | "unauthenticated";

interface AuthState {
  user: User | null;
  preferences: UserPreferences | null;
  status: Status;
  hydrate: () => Promise<void>;
  login: (email: string, password: string) => Promise<void>;
  register: (payload: RegisterPayload) => Promise<void>;
  logout: () => Promise<void>;
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  preferences: null,
  status: "idle",

  hydrate: async () => {
    set({ status: "loading" });
    try {
      const { user, preferences } = await authApi.me();
      set({ user, preferences, status: "authenticated" });
    } catch {
      set({ user: null, preferences: null, status: "unauthenticated" });
    }
  },

  login: async (email, password) => {
    const { user, preferences } = await authApi.login(email, password);
    set({ user, preferences, status: "authenticated" });
  },

  register: async (payload) => {
    const { user, preferences } = await authApi.register(payload);
    set({ user, preferences, status: "authenticated" });
  },

  logout: async () => {
    try {
      await authApi.logout();
    } catch (err) {
      if (!(err instanceof ApiError)) throw err;
    }
    set({ user: null, preferences: null, status: "unauthenticated" });
  },
}));
