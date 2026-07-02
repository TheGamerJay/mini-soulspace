"use client";

import type { ReactNode } from "react";

interface FormFieldProps {
  label: string;
  htmlFor?: string;
  error?: string;
  children: ReactNode;
}

/** Label + control + inline error message. */
export function FormField({ label, htmlFor, error, children }: FormFieldProps) {
  return (
    <div className="flex flex-col gap-1.5">
      <label htmlFor={htmlFor} className="text-sm font-medium text-soul-accent">
        {label}
      </label>
      {children}
      {error && <p className="text-sm text-red-400">{error}</p>}
    </div>
  );
}

/** Shared text/select input styling. */
export const inputClass =
  "w-full rounded-lg border border-soul-primary/30 bg-soul-surface px-4 py-2.5 text-soul-accent outline-none focus:border-soul-primary";
