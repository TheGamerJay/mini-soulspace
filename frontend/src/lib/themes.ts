/**
 * Companion Themes (Phase 4.1).
 *
 * Themes ONLY affect appearance — never Mini's personality, memory, safety or
 * behavior. Implemented themes have a CSS variable block in globals.css;
 * architecture-ready themes are registered here and plug in later by adding
 * their variable block (no redesign).
 */

export interface CompanionTheme {
  id: string;
  label: string;
  implemented: boolean;
  description: string;
}

export const THEMES: CompanionTheme[] = [
  { id: "midnight", label: "Midnight", implemented: true, description: "Deep violet night — the classic SoulSpace." },
  { id: "parchment", label: "Classic Parchment", implemented: true, description: "Warm paper, brown ink, timeless." },
  { id: "galaxy", label: "Galaxy", implemented: true, description: "Starlit purples and soft nebula light." },
  // Architecture-ready (variable blocks land in a future phase):
  { id: "morning-light", label: "Morning Light", implemented: false, description: "Soft dawn tones." },
  { id: "autumn", label: "Autumn", implemented: false, description: "Amber leaves and warm shadows." },
  { id: "winter", label: "Winter", implemented: false, description: "Quiet blues and frost." },
  { id: "spring", label: "Spring", implemented: false, description: "Fresh greens and light." },
  { id: "rainy-day", label: "Rainy Day", implemented: false, description: "Grey skies, cozy pages." },
];

export const DEFAULT_THEME = "midnight";
const STORAGE_KEY = "soulspace-theme";

export function getStoredTheme(): string {
  if (typeof window === "undefined") return DEFAULT_THEME;
  const stored = window.localStorage.getItem(STORAGE_KEY);
  const theme = THEMES.find((t) => t.id === stored && t.implemented);
  return theme ? theme.id : DEFAULT_THEME;
}

export function applyTheme(id: string): void {
  const theme = THEMES.find((t) => t.id === id && t.implemented);
  const resolved = theme ? theme.id : DEFAULT_THEME;
  document.documentElement.dataset.theme = resolved;
  window.localStorage.setItem(STORAGE_KEY, resolved);
}
