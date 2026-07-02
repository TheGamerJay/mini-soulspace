"use client";

import { forwardRef, useState } from "react";

type PasswordInputProps = Omit<
  React.InputHTMLAttributes<HTMLInputElement>,
  "type"
>;

/**
 * Password field with a custom show/hide toggle.
 *
 * Per product spec, the native browser reveal icon is suppressed (see
 * globals.css) and replaced everywhere with 🙈 (hidden) / 👁️ (visible).
 */
export const PasswordInput = forwardRef<HTMLInputElement, PasswordInputProps>(
  function PasswordInput({ className = "", ...props }, ref) {
    const [visible, setVisible] = useState(false);

    return (
      <div className="relative">
        <input
          {...props}
          ref={ref}
          type={visible ? "text" : "password"}
          className={`w-full rounded-lg border border-soul-primary/30 bg-soul-surface px-4 py-2.5 pr-12 text-soul-accent outline-none focus:border-soul-primary ${className}`}
        />
        <button
          type="button"
          aria-label={visible ? "Hide password" : "Show password"}
          aria-pressed={visible}
          onClick={() => setVisible((v) => !v)}
          className="absolute right-2 top-1/2 -translate-y-1/2 rounded-md px-2 py-1 text-lg leading-none"
        >
          {visible ? "👁️" : "🙈"}
        </button>
      </div>
    );
  },
);
