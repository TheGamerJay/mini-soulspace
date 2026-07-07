"use client";

import { AnimatePresence, motion } from "framer-motion";
import { usePathname, useRouter } from "next/navigation";
import { useCallback, useEffect, useRef, useState } from "react";

import { ApiError, soulApi } from "@/lib/api";
import { parseSoulPath } from "@/lib/soulPath";
import type { Reflection, SoulPage } from "@/lib/types";

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
    // Let the book-closing animation play, then slide back onto the shelf.
    setTimeout(() => router.push("/soul-library"), 650);
  }, [router]);

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
          {!closing && (
            <>
              <button
                onClick={() => save(false)}
                className="rounded-full border border-soul-primary/40 px-5 py-1.5 text-sm font-semibold text-soul-primary transition-colors hover:text-soul-accent"
              >
                Save
              </button>
              <button
                onClick={closeSoulDiary}
                className="rounded-full bg-soul-primary px-5 py-1.5 text-sm font-semibold text-white transition-colors hover:bg-soul-accent"
              >
                Close SoulDiary
              </button>
            </>
          )}
        </div>
      </div>

      {/* Journal page (with the ribbon bookmark once closed) */}
      <div className="relative overflow-hidden rounded-2xl border border-soul-primary/20 bg-soul-surface/60 p-6 shadow-xl">
        <AnimatePresence>
          {closeState === "reflected" || closeState === "shelving" ? (
            <motion.div
              key="ribbon"
              aria-label="Ribbon bookmark"
              initial={{ y: -160, opacity: 0 }}
              animate={{ y: 0, opacity: 1 }}
              transition={{ duration: 0.9, ease: "easeOut", delay: 0.3 }}
              className="absolute right-8 top-0 h-24 w-4 rounded-b-md bg-gradient-to-b from-soul-primary to-soul-accent shadow-lg"
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
      </div>

      <div className="mt-4 flex flex-wrap justify-between gap-4 text-sm text-soul-muted">
        <span>Created: {fmt(page.created_at)}</span>
        <span>Updated: {fmt(updatedAt)}</span>
        <span>
          {wordCount} words · {charCount} characters
        </span>
      </div>

      {/* The reflection layer: the SoulDiary talks back (Phase 4.0). */}
      <section data-slot="ai-reflection" className="mt-8">
        {closeState === "open" && (
          <div className="rounded-2xl border border-dashed border-soul-primary/15 p-4 text-center text-xs text-soul-muted/60">
            When you close your SoulDiary, it will reflect on what you wrote.
          </div>
        )}
        {closeState === "closing" && (
          <div
            role="status"
            className="animate-pulse rounded-2xl border border-soul-primary/20 bg-soul-surface/40 p-6 text-center text-sm text-soul-muted"
          >
            Your SoulDiary is reading your words…
          </div>
        )}
        {(closeState === "reflected" || closeState === "shelving") && (
          <motion.div
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.7, ease: "easeOut" }}
            className="rounded-2xl border border-soul-primary/25 bg-soul-surface/70 p-6 shadow-lg"
          >
            <p className="mb-2 text-xs font-semibold uppercase tracking-wider text-soul-primary">
              Your SoulDiary reflects
            </p>
            {reflection?.delivered ? (
              <p className="whitespace-pre-wrap font-serif text-lg leading-relaxed text-soul-accent">
                {reflection.text}
              </p>
            ) : (
              <p className="font-serif text-lg leading-relaxed text-soul-muted">
                Your words are safely kept in your SoulDiary. A reflection will be
                waiting another time.
              </p>
            )}
            {reflection?.memory_updates?.length ? (
              <p className="mt-4 text-xs text-soul-muted">
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
