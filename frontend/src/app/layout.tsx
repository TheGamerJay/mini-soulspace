import type { Metadata } from "next";
import "@/styles/globals.css";

export const metadata: Metadata = {
  title: "Mini SoulSpace",
  description: "Your personal SoulDiary — a diary that talks back.",
};

// Applies the stored Companion Theme before first paint (no flash).
const themeInit = `try{var t=localStorage.getItem("soulspace-theme");document.documentElement.dataset.theme=(t==="parchment"||t==="galaxy")?t:"midnight";}catch(e){}`;

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en" data-theme="midnight">
      <body>
        <script dangerouslySetInnerHTML={{ __html: themeInit }} />
        {children}
      </body>
    </html>
  );
}
