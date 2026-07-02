"use client";

import { motion } from "framer-motion";
import { useRouter } from "next/navigation";
import { PrimaryButton } from "@/components/PrimaryButton";

export default function LandingPage() {
  const router = useRouter();
  return (
    <main className="flex min-h-screen flex-col items-center justify-center bg-gradient-to-b from-soul-bg to-soul-surface px-6 text-center">
      <motion.h1
        initial={{ opacity: 0, y: 24 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6, ease: "easeOut" }}
        className="bg-gradient-to-r from-soul-primary to-soul-accent bg-clip-text text-6xl font-extrabold tracking-tight text-transparent sm:text-7xl"
      >
        Mini SoulSpace
      </motion.h1>

      <motion.p
        initial={{ opacity: 0, y: 16 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6, delay: 0.15, ease: "easeOut" }}
        className="mt-6 max-w-xl text-xl leading-relaxed text-soul-muted"
      >
        Your personal SoulDiary —
        <br />A diary that talks back.
      </motion.p>

      <motion.div
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6, delay: 0.3, ease: "easeOut" }}
        className="mt-12"
      >
        <PrimaryButton onClick={() => router.push("/home")}>Open My SoulDiary</PrimaryButton>
      </motion.div>
    </main>
  );
}
