"use client";

import { motion } from "framer-motion";
import { usePathname, useRouter } from "next/navigation";
import { useCallback, useEffect, useState } from "react";

import { PrimaryButton } from "@/components/PrimaryButton";
import { ApiError, soulApi } from "@/lib/api";
import { parseSoulPath } from "@/lib/soulPath";
import type { SoulBook, SoulChapter } from "@/lib/types";
import { useAuthStore } from "@/stores/authStore";

export function BookScreen() {
  const router = useRouter();
  const pathname = usePathname();
  const { bookId } = parseSoulPath(pathname);
  const ownerName = useAuthStore((s) => s.user?.display_name ?? "SoulSpace");

  const [book, setBook] = useState<SoulBook | null>(null);
  const [chapters, setChapters] = useState<SoulChapter[]>([]);
  const [newTitle, setNewTitle] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    if (!bookId) return;
    setLoading(true);
    try {
      const [b, chs] = await Promise.all([
        soulApi.getBook(bookId),
        soulApi.listChapters(bookId),
      ]);
      setBook(b);
      setChapters(chs);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not open this SoulBook.");
    } finally {
      setLoading(false);
    }
  }, [bookId]);

  useEffect(() => {
    load();
  }, [load]);

  const addChapter = async (title: string) => {
    if (!bookId || !title.trim()) return;
    const chapter = await soulApi.createChapter(bookId, { title: title.trim() });
    setNewTitle("");
    router.push(`/soulbooks/${bookId}/chapters/${chapter.id}`);
  };

  if (loading) return <Centered>Opening your SoulBook…</Centered>;
  if (error || !book) return <Centered>{error ?? "Not found."}</Centered>;

  const year = new Date().getFullYear();

  return (
    <main className="mx-auto min-h-screen max-w-3xl px-6 py-10">
      <button onClick={() => router.push("/soul-library")} className="mb-6 text-sm text-soul-primary hover:text-soul-accent">
        ← Soul Library
      </button>

      {/* Book cover / opening animation */}
      <motion.div
        initial={{ opacity: 0, rotateX: -12, y: 20 }}
        animate={{ opacity: 1, rotateX: 0, y: 0 }}
        transition={{ duration: 0.6, ease: "easeOut" }}
        className="mb-10 rounded-3xl border border-soul-primary/30 bg-gradient-to-b from-soul-surface to-soul-bg p-12 text-center shadow-2xl"
      >
        <p className="text-sm uppercase tracking-[0.3em] text-soul-muted">SoulDiary</p>
        <h1 className="mt-4 text-4xl font-extrabold text-soul-accent">{book.title}</h1>
        <p className="mt-6 text-lg text-soul-primary">{ownerName}</p>
        <p className="mt-1 text-soul-muted">{year}</p>
        {book.description && <p className="mt-4 text-sm text-soul-muted">{book.description}</p>}
      </motion.div>

      <div className="mb-6 flex flex-wrap items-center gap-3">
        <input
          aria-label="New chapter title"
          value={newTitle}
          onChange={(e) => setNewTitle(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && addChapter(newTitle)}
          placeholder="Name a new chapter…"
          className="flex-1 rounded-lg border border-soul-primary/30 bg-soul-surface px-4 py-2.5 text-soul-accent outline-none focus:border-soul-primary"
        />
        <PrimaryButton onClick={() => addChapter(newTitle)} disabled={!newTitle.trim()}>
          Add Chapter
        </PrimaryButton>
      </div>

      <h2 className="mb-3 text-xl font-semibold text-soul-accent">Chapters</h2>
      {chapters.length === 0 && <p className="text-soul-muted">No chapters yet — add your first above.</p>}
      <ul className="flex flex-col gap-3">
        {chapters.map((ch) => (
          <motion.li key={ch.id} whileHover={{ x: 4 }}>
            <button
              onClick={() => router.push(`/soulbooks/${bookId}/chapters/${ch.id}`)}
              className="flex w-full items-center justify-between rounded-xl border border-soul-primary/20 bg-soul-surface px-5 py-4 text-left transition-colors hover:border-soul-primary"
            >
              <span className="text-soul-accent">
                <span className="text-soul-muted">Chapter {ch.chapter_number} · </span>
                {ch.title}
              </span>
              <span className="text-sm text-soul-muted">
                {ch.page_count} page{ch.page_count === 1 ? "" : "s"}
              </span>
            </button>
          </motion.li>
        ))}
      </ul>
    </main>
  );
}

function Centered({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex min-h-screen items-center justify-center text-soul-muted">{children}</div>
  );
}
