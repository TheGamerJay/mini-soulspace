import type { Metadata } from "next";
import { AuthGuard } from "@/components/AuthGuard";
import { SoulLibrary } from "@/features/soulbook/SoulLibrary";

export const metadata: Metadata = {
  title: "Soul Library — Mini SoulSpace",
};

export default function SoulLibraryPage() {
  return (
    <AuthGuard>
      <SoulLibrary />
    </AuthGuard>
  );
}
