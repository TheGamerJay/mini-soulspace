import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/features/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        // Theme-aware palette: every color resolves through CSS variables so
        // Companion Themes restyle the whole SoulDiary without redesign.
        soul: {
          bg: "var(--soul-bg)",
          surface: "var(--soul-surface)",
          primary: "var(--soul-primary)",
          accent: "var(--soul-accent)",
          muted: "var(--soul-muted)",
          ink: "var(--soul-ink)",
          paper: "var(--soul-paper)",
        },
      },
      fontFamily: {
        sans: ["var(--font-sans)", "system-ui", "sans-serif"],
        reflection: ["var(--font-reflection)", "Georgia", "serif"],
      },
    },
  },
  plugins: [],
};

export default config;
