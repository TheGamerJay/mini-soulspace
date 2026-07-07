"use client";

import { useMemo } from "react";

/**
 * Ink gradually appears, as though an invisible fountain pen is writing inside
 * the journal. Not typing, not streaming — words fade in like drying ink.
 * Honors prefers-reduced-motion (globals.css shows everything instantly).
 */
export function InkText({ text, className = "" }: { text: string; className?: string }) {
  const words = useMemo(() => text.split(/(\s+)/), [text]);
  // Pace the pen: quick enough to feel alive, capped so long reflections
  // finish within ~8 seconds.
  const step = Math.min(0.09, 8 / Math.max(words.length, 1));

  return (
    <p aria-label={text} className={`whitespace-pre-wrap ${className}`}>
      {words.map((word, i) =>
        /^\s+$/.test(word) ? (
          <span key={i}>{word}</span>
        ) : (
          <span
            key={i}
            aria-hidden
            className="ink-word"
            style={{ animationDelay: `${(i * step).toFixed(2)}s` }}
          >
            {word}
          </span>
        ),
      )}
    </p>
  );
}
