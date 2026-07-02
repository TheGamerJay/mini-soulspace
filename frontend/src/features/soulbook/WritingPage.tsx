"use client";

import { motion } from "framer-motion";
import { usePathname, useRouter } from "next/navigation";
import { useCallback, useEffect, useRef, useState } from "react";

import { ApiError, soulApi } from "@/lib/api";
import { parseSoulPath } from "@/lib/soulPath";
import type { SoulPage } from "@/lib/types";

type SaveStatus = "saved" | "saving" | "unsaved" | "failed";

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

  const loadedRef = useRef(false);
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

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

  return (
    <motion.main
      initial={{ opacity: 0, x: 30 }}
      animate={{ opacity: 1, x: 0 }}
      exit={{ opacity: 0, x: -30 }}
      transition={{ duration: 0.4, ease: "easeOut" }}
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
          <button
            onClick={() => save(false)}
            className="rounded-full bg-soul-primary px-5 py-1.5 text-sm font-semibold text-white transition-colors hover:bg-soul-accent"
          >
            Save
          </button>
        </div>
      </div>

      {/* Journal page */}
      <div className="rounded-2xl border border-soul-primary/20 bg-soul-surface/60 p-6 shadow-xl">
        <input
          aria-label="Page title"
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          placeholder="Title this page…"
          className="mb-4 w-full border-b border-soul-primary/20 bg-transparent pb-2 text-2xl font-semibold text-soul-accent outline-none"
        />
        <textarea
          aria-label="Writing area"
          value={content}
          onChange={(e) => setContent(e.target.value)}
          placeholder="Dear Diary..."
          spellCheck
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

      {/* Reserved for a future AI reflection layer (Phase 3+): user writing → AI
          reflection → follow-up conversation. Intentionally empty in Phase 2. */}
      <section
        aria-hidden
        data-slot="ai-reflection"
        className="mt-8 rounded-2xl border border-dashed border-soul-primary/15 p-4 text-center text-xs text-soul-muted/60"
      >
        Reflections will appear here in a future chapter of SoulSpace.
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
