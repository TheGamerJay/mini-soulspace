"use client";

import { useEffect, useState } from "react";

import { DEFAULT_THEME, THEMES, applyTheme, getStoredTheme } from "@/lib/themes";

/** Companion Theme picker — appearance only, never behavior. */
export function ThemeSwitcher() {
  const [theme, setTheme] = useState(DEFAULT_THEME);

  useEffect(() => {
    const stored = getStoredTheme();
    setTheme(stored);
    applyTheme(stored);
  }, []);

  const select = (id: string) => {
    setTheme(id);
    applyTheme(id);
  };

  return (
    <label className="flex items-center gap-2 text-sm text-soul-muted">
      <span aria-hidden>🎨</span>
      <span className="sr-only">Companion theme</span>
      <select
        aria-label="Companion theme"
        value={theme}
        onChange={(e) => select(e.target.value)}
        className="rounded-lg border border-soul-primary/30 bg-soul-surface px-2 py-1 text-soul-accent"
      >
        {THEMES.filter((t) => t.implemented).map((t) => (
          <option key={t.id} value={t.id}>
            {t.label}
          </option>
        ))}
      </select>
    </label>
  );
}
