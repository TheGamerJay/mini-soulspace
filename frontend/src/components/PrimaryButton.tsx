"use client";

import { motion } from "framer-motion";
import type { ReactNode } from "react";

interface PrimaryButtonProps {
  children: ReactNode;
  onClick?: () => void;
  type?: "button" | "submit";
  disabled?: boolean;
  className?: string;
}

/** The primary call-to-action button used across SoulSpace. */
export function PrimaryButton({
  children,
  onClick,
  type = "button",
  disabled = false,
  className = "",
}: PrimaryButtonProps) {
  return (
    <motion.button
      type={type}
      onClick={onClick}
      disabled={disabled}
      whileHover={disabled ? undefined : { scale: 1.04 }}
      whileTap={disabled ? undefined : { scale: 0.97 }}
      className={`rounded-full bg-soul-primary px-8 py-3 text-lg font-semibold text-white shadow-lg shadow-soul-primary/30 transition-colors hover:bg-soul-accent disabled:cursor-not-allowed disabled:opacity-40 disabled:hover:bg-soul-primary ${className}`}
    >
      {children}
    </motion.button>
  );
}
