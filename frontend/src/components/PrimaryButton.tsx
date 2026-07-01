"use client";

import { motion } from "framer-motion";
import type { ReactNode } from "react";

interface PrimaryButtonProps {
  children: ReactNode;
  onClick?: () => void;
}

/** The primary call-to-action button used across SoulSpace. */
export function PrimaryButton({ children, onClick }: PrimaryButtonProps) {
  return (
    <motion.button
      type="button"
      onClick={onClick}
      whileHover={{ scale: 1.04 }}
      whileTap={{ scale: 0.97 }}
      className="rounded-full bg-soul-primary px-8 py-3 text-lg font-semibold text-white shadow-lg shadow-soul-primary/30 transition-colors hover:bg-soul-accent"
    >
      {children}
    </motion.button>
  );
}
