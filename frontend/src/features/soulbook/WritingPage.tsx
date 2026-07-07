"use client";

import { AnimatePresence, motion, useReducedMotion } from "framer-motion";
import { usePathname, useRouter } from "next/navigation";
import { useCallback, useEffect, useRef, useState } from "react";

import { InkText } from "@/components/InkText";
import { ApiError, soulApi } from "@/lib/api";
import { parseSoulPath } from "@/lib/soulPath";
import type { Reflection, SoulBook, SoulPage } from "@/lib/types";

type SaveStatus = "saved" | "saving" | "unsaved" | "failed";
type CloseState = "open" | "closing" | "reflected" | "shelving";

const STATUS_LABEL: Record<SaveStatus, string> = {
  saved: "Saved",
  saving: "Saving…",
  unsaved: "Unsaved changes",
  failed: "Save failed",
};

const AUTOSAVE_DELAY = 1200;

function fmt(ts: string | null): string {
  if (!ts) return "—";
  return new Date(ts).toLocaleString();
}

export function WritingPage() {
  const router = useRouter();
  const pathname = usePathname();
  const { bookId, chapterId, pageId } = parseSoulPath(pathname);

  const [page, setPage] = useState<SoulPage | null>(null);
  const [title, setTitle] = useState("");
  const [content, setContent] = useState("");
  const [status, setStatus] = useState<SaveStatus>("saved");
  const [updatedAt, setUpdatedAt] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [closeState, setCloseState] = useState<CloseState>("open");
  const [reflection, setReflection] = useState<Reflection | null>(null);
  const [book, setBook] = useState<SoulBook | null>(null);
  const reduceMotion = useReducedMotion();

  const loadedRef = useRef(false);
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const cursorRef = useRef<HTMLTextAreaElement | null>(null);

  const wordCount = content.trim() ? content.trim().split(/\s+/).length : 0;
  const charCount = content.length;

  useEffect(() => {
    if (!bookId || !chapterId || !pageId) return;
    soulApi
      .getPage(bookId, chapterId, pageId)
      .then((p) => {
        setPage(p);
        setTitle(p.title);
        setContent(p.content);
        setUpdatedAt(p.updated_at);
        setStatus("saved");
        loadedRef.current = true;
      })
      .catch((err) =>
        setError(err instanceof ApiError ? err.message : "Could not open this page."),
      )
      .finally(() => setLoading(false));
    // The book's personalization (ribbon color) shapes the closing experience.
    soulApi.getBook(bookId).then(setBook).catch(() => setBook(null));
  }, [bookId, chapterId, pageId]);

  const save = useCallback(
    async (auto: boolean) => {
      if (!bookId || !chapterId || !pageId) return;
      setStatus("saving");
      try {
        if (auto) {
          const res = await soulApi.autosavePage(bookId, chapterId, pageId, { title, content });
          setUpdatedAt(res.updated_at);
        } else {
          const res = await soulApi.updatePage(bookId, chapterId, pageId, { title, content });
          setUpdatedAt(res.updated_at);
        }
        setStatus("saved");
      } catch {
        setStatus("failed");
      }
    },
    [bookId, chapterId, pageId, title, content],
  );

  // Debounced auto-save on change (skips the initial load).
  useEffect(() => {
    if (!loadedRef.current) return;
    setStatus("unsaved");
    if (timerRef.current) clearTimeout(timerRef.current);
    timerRef.current = setTimeout(() => save(true), AUTOSAVE_DELAY);
    return () => {
      if (timerRef.current) clearTimeout(timerRef.current);
    };
  }, [title, content, save]);

  // Close SoulDiary: save → the Orchestra reflects → ribbon bookmark → shelf.
  const closeSoulDiary = useCallback(async () => {
    if (!bookId || !chapterId || !pageId || closeState !== "open") return;
    if (timerRef.current) clearTimeout(timerRef.current);
    setCloseState("closing");
    try {
      const res = await soulApi.closePage(bookId, chapterId, pageId, {
        title,
        content,
        cursor: cursorRef.current?.selectionStart ?? content.length,
      });
      setStatus("saved");
      setUpdatedAt(new Date().toISOString());
      setReflection(res.reflection);
    } catch {
      // The page auto-saves continuously; the diary entry is never lost.
      setReflection(null);
    }
    setCloseState("reflected");
  }, [bookId, chapterId, pageId, title, content, closeState]);

  const returnToShelf = useCallback(() => {
    setCloseState("shelving");
    // Let the book close and slide back onto the shelf — never rushed.
    setTimeout(() => router.push("/soul-library"), reduceMotion ? 50 : 900);
  }, [router, reduceMotion]);

  // Guard against losing unsaved work.
  useEffect(() => {
    const handler = (e: BeforeUnloadEvent) => {
      if (status === "unsaved" || status === "saving") {
        e.preventDefault();
        e.returnValue = "";
      }
    };
    window.addEventListener("beforeunload", handler);
    return () => window.removeEventListener("beforeunload", handler);
  }, [status]);

  if (loading) return <Centered>Opening your page…</Centered>;
  if (error || !page) return <Centered>{error ?? "Not found."}</Centered>;

  const closing = closeState !== "open";

  return (
    <motion.main
      initial={{ opacity: 0, x: 30 }}
      animate={
        closeState === "shelving"
          ? { opacity: 0, scale: 0.85, rotateY: 25, x: -80 }
          : { opacity: 1, x: 0, scale: 1 }
      }
      exit={{ opacity: 0, x: -30 }}
      transition={{ duration: 0.6, ease: "easeInOut" }}
      className="mx-auto min-h-screen max-w-3xl scroll-smooth px-6 py-8"
    >
      <div className="mb-4 flex items-center justify-between">
        <button
          onClick={() => router.push(`/soulbooks/${bookId}/chapters/${chapterId}`)}
          className="text-sm text-soul-primary hover:text-soul-accent"
        >
          ← Back to chapter
        </button>
        <div className="flex items-center gap-3">
          <StatusPill status={status} />
          <AnimatePresence>
            {!closing && (
              <motion.div exit={{ opacity: 0 }} transition={{ duration: 0.5 }} className="flex gap-3">
                <button
                  onClick={() => save(false)}
                  className="rounded-full border border-soul-primary/40 px-5 py-1.5 text-sm font-semibold text-soul-primary transition-colors hover:text-soul-accent"
                >
                  Save
                </button>
                <button
                  onClick={closeSoulDiary}
                  className="rounded-full bg-soul-primary px-5 py-1.5 text-sm font-semibold text-white transition-all hover:bg-soul-accent hover:shadow-lg"
                >
                  Save &amp; Close
                </button>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </div>

      {/* Journal page: soft page-turn on close, ribbon in the book's color */}
      <motion.div
        animate={
          closeState === "closing" && !reduceMotion
            ? { rotateY: [0, -7, 0], transition: { duration: 1.1, ease: "easeInOut" } }
            : {}
        }
        style={{ transformPerspective: 1200 }}
        className={`relative overflow-hidden rounded-2xl border border-soul-primary/20 bg-soul-paper/80 p-6 shadow-xl ${
          closeState === "closing" ? "companion-glow" : ""
        }`}
      >
        <AnimatePresence>
          {closeState === "reflected" || closeState === "shelving" ? (
            <motion.div
              key="ribbon"
              aria-label="Ribbon bookmark"
              initial={{ y: -160, opacity: 0 }}
              animate={{ y: 0, opacity: 1 }}
              transition={{ duration: 1.1, ease: "easeOut", delay: 0.4 }}
              style={{ backgroundColor: book?.ribbon_color ?? "#e0b64c" }}
              className="absolute right-8 top-0 h-24 w-4 rounded-b-md shadow-lg"
            />
          ) : null}
        </AnimatePresence>
        <input
          aria-label="Page title"
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          placeholder="Title this page…"
          readOnly={closing}
          className="mb-4 w-full border-b border-soul-primary/20 bg-transparent pb-2 text-2xl font-semibold text-soul-accent outline-none"
        />
        <textarea
          ref={cursorRef}
          aria-label="Writing area"
          value={content}
          onChange={(e) => setContent(e.target.value)}
          placeholder="Dear Diary..."
          spellCheck
          readOnly={closing}
          className="min-h-[50vh] w-full resize-none bg-transparent font-serif text-lg leading-relaxed text-soul-accent outline-none placeholder:text-soul-muted"
        />
      </motion.div>

      <div className="mt-4 flex flex-wrap justify-between gap-4 text-sm text-soul-muted">
        <span>Created: {fmt(page.created_at)}</span>
        <span>Updated: {fmt(updatedAt)}</span>
        <span>
          {wordCount} words · {charCount} characters
        </span>
      </div>

      {/* The reflection layer: journal writing, never chat (Rule 22). */}
      <section data-slot="ai-reflection" className="mt-8">
        {closeState === "open" && (
          <div className="rounded-2xl border border-dashed border-soul-primary/15 p-4 text-center text-xs text-soul-muted/60">
            When you close your SoulDiary, it will quietly reflect with you.
          </div>
        )}
        {closeState === "closing" && (
          /* A subtle companion glow — no spinners, no typing bubbles. */
          <div role="status" className="flex justify-center py-10">
            <span className="sr-only">Your SoulDiary is reflecting.</span>
            <span aria-hidden className="companion-glow inline-block rounded-full bg-soul-paper px-6 py-3 text-2xl">
              ❧
            </span>
          </div>
        )}
        {(closeState === "reflected" || closeState === "shelving") && (
          <motion.div
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.9, ease: "easeOut" }}
            className="rounded-2xl border border-soul-primary/20 bg-soul-paper/80 px-8 py-7 shadow-lg"
          >
            {/* Soft divider with a decorative flourish */}
            <div className="mb-5 flex items-center gap-4" aria-hidden>
              <span className="h-px flex-1 bg-gradient-to-r from-transparent via-soul-primary/40 to-transparent" />
              <span className="text-soul-primary/70">❦</span>
              <span className="h-px flex-1 bg-gradient-to-r from-transparent via-soul-primary/40 to-transparent" />
            </div>
            {reflection?.delivered ? (
              <InkText
                text={reflection.text}
                className="font-reflection text-lg leading-loose text-soul-ink"
              />
            ) : (
              <p className="font-reflection text-lg leading-loose text-soul-muted">
                Your words are safely kept in your SoulDiary. A reflection will be
                waiting another time.
              </p>
            )}
            {/* Companion seal */}
            <p aria-hidden className="mt-4 text-right text-soul-primary/60">
              ✒
            </p>
            {reflection?.memory_updates?.length ? (
              <p className="mt-1 text-xs text-soul-muted">
                🕮 A memory was {reflection.memory_updates[0].op === "update" ? "updated" : "kept"}.
              </p>
            ) : null}
            <div className="mt-6 text-center">
              <button
                onClick={returnToShelf}
                className="rounded-full bg-soul-primary px-6 py-2 text-sm font-semibold text-white transition-colors hover:bg-soul-accent"
              >
                Return to the shelf
              </button>
            </div>
          </motion.div>
        )}
      </section>
    </motion.main>
  );
}

function StatusPill({ status }: { status: SaveStatus }) {
  const color =
    status === "saved"
      ? "text-green-400"
      : status === "failed"
        ? "text-red-400"
        : "text-soul-muted";
  return <span className={`text-sm ${color}`}>{STATUS_LABEL[status]}</span>;
}

function Centered({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex min-h-screen items-center justify-center text-soul-muted">{children}</div>
  );
}
