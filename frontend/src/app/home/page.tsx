"use client";

import { motion } from "framer-motion";
import { useRouter } from "next/navigation";
import { useState } from "react";

import { AuthGuard } from "@/components/AuthGuard";
import { PrimaryButton } from "@/components/PrimaryButton";
import { useAuthStore } from "@/stores/authStore";

function HomeContent() {
  const router = useRouter();
  const user = useAuthStore((s) => s.user);
  const logout = useAuthStore((s) => s.logout);
  const [comingSoon, setComingSoon] = useState(false);

  const firstName = user?.display_name?.split(" ")[0] ?? "friend";

  return (
    <main className="flex min-h-screen flex-col items-center justify-center bg-gradient-to-b from-soul-bg to-soul-surface px-6 text-center">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6, ease: "easeOut" }}
        className="flex flex-col items-center"
      >
        <h1 className="text-4xl font-bold text-soul-accent sm:text-5xl">
          Welcome back, {firstName}.
        </h1>
        <p className="mt-4 text-xl text-soul-muted">Ready to continue your story?</p>

        <div className="mt-10">
          <PrimaryButton onClick={() => setComingSoon(true)}>Open My SoulDiary</PrimaryButton>
        </div>

        {comingSoon && (
          <motion.p
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="mt-6 max-w-md text-soul-muted"
          >
            Your SoulDiary is being prepared. Writing &amp; reflections arrive in{" "}
            <span className="text-soul-primary">Phase 2</span> — your account and story are
            ready and waiting. 💜
          </motion.p>
        )}

        <div className="mt-12 flex items-center gap-6 text-sm text-soul-muted">
          <button onClick={() => router.push("/profile")} className="hover:text-soul-accent">
            Profile
          </button>
          <button
            onClick={async () => {
              await logout();
              router.replace("/login");
            }}
            className="hover:text-soul-accent"
          >
            Log out
          </button>
        </div>
      </motion.div>
    </main>
  );
}

export default function HomePage() {
  return (
    <AuthGuard>
      <HomeContent />
    </AuthGuard>
  );
}
