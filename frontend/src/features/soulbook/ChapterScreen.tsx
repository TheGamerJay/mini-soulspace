"use client";

import { motion } from "framer-motion";
import { usePathname, useRouter } from "next/navigation";
import { useCallback, useEffect, useState } from "react";

import { PrimaryButton } from "@/components/PrimaryButton";
import { ApiError, soulApi } from "@/lib/api";
import { parseSoulPath } from "@/lib/soulPath";
import type { SoulChapter, SoulPage } from "@/lib/types";

export function ChapterScreen() {
  const router = useRouter();
  const pathname = usePathname();
  const { bookId, chapterId } = parseSoulPath(pathname);

  const [chapter, setChapter] = useState<SoulChapter | null>(null);
  const [pages, setPages] = useState<SoulPage[]>([]);
  const [newTitle, setNewTitle] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    if (!bookId || !chapterId) return;
    setLoading(true);
    try {
      const [ch, pgs] = await Promise.all([
        soulApi.getChapter(bookId, chapterId),
        soulApi.listPages(bookId, chapterId),
      ]);
      setChapter(ch);
      setPages(pgs);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not open this chapter.");
    } finally {
      setLoading(false);
    }
  }, [bookId, chapterId]);

  useEffect(() => {
    load();
  }, [load]);

  const addPage = async () => {
    if (!bookId || !chapterId) return;
    const title = newTitle.trim() || `Page ${pages.length + 1}`;
    const page = await soulApi.createPage(bookId, chapterId, { title });
    router.push(`/soulbooks/${bookId}/chapters/${chapterId}/pages/${page.id}`);
  };

  if (loading) return <Centered>Turning the page…</Centered>;
  if (error || !chapter) return <Centered>{error ?? "Not found."}</Centered>;

  return (
    <main className="mx-auto min-h-screen max-w-3xl px-6 py-10">
      <button
        onClick={() => router.push(`/soulbooks/${bookId}`)}
        className="mb-6 text-sm text-soul-primary hover:text-soul-accent"
      >
        ← Back to SoulBook
      </button>

      <motion.h1
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        className="text-3xl font-bold text-soul-accent"
      >
        <span className="text-soul-muted">Chapter {chapter.chapter_number}: </span>
        {chapter.title}
      </motion.h1>

      <div className="my-6 flex flex-wrap items-center gap-3">
        <input
          aria-label="New page title"
          value={newTitle}
          onChange={(e) => setNewTitle(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && addPage()}
          placeholder="Name a new page (optional)…"
          className="flex-1 rounded-lg border border-soul-primary/30 bg-soul-surface px-4 py-2.5 text-soul-accent outline-none focus:border-soul-primary"
        />
        <PrimaryButton onClick={addPage}>New Page</PrimaryButton>
      </div>

      <h2 className="mb-3 text-xl font-semibold text-soul-accent">Pages</h2>
      {pages.length === 0 && <p className="text-soul-muted">No pages yet — start writing above.</p>}
      <ul className="flex flex-col gap-3">
        {pages.map((p) => (
          <motion.li key={p.id} whileHover={{ x: 4 }}>
            <button
              onClick={() =>
                router.push(`/soulbooks/${bookId}/chapters/${chapterId}/pages/${p.id}`)
              }
              className="flex w-full items-center justify-between rounded-xl border border-soul-primary/20 bg-soul-surface px-5 py-4 text-left transition-colors hover:border-soul-primary"
            >
              <span className="text-soul-accent">
                <span className="text-soul-muted">Page {p.page_number} · </span>
                {p.title}
              </span>
              <span className="text-sm text-soul-muted">{p.word_count} words</span>
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
