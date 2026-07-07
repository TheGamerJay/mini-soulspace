"use client";

import { AnimatePresence, motion } from "framer-motion";
import { useRouter } from "next/navigation";
import { useCallback, useEffect, useState } from "react";

import { PrimaryButton } from "@/components/PrimaryButton";
import { ApiError, soulApi } from "@/lib/api";
import type { Bookmark, SoulBook, SortOption } from "@/lib/types";

const SORTS: { value: SortOption; label: string }[] = [
  { value: "recently_opened", label: "Recently Opened" },
  { value: "recently_updated", label: "Recently Updated" },
  { value: "alphabetical", label: "Alphabetical" },
  { value: "newest", label: "Newest" },
  { value: "oldest", label: "Oldest" },
];

const EXAMPLES = [
  "Personal Journal",
  "Dream Journal",
  "Song Ideas",
  "Story Ideas",
  "Gratitude Journal",
  "Travel Journal",
  "Project Journal",
];

export function SoulLibrary() {
  const router = useRouter();
  const [books, setBooks] = useState<SoulBook[]>([]);
  const [sort, setSort] = useState<SortOption>("recently_opened");
  const [showArchived, setShowArchived] = useState(false);
  const [query, setQuery] = useState("");
  const [newTitle, setNewTitle] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [bookmark, setBookmark] = useState<Bookmark | null>(null);

  // The ribbon bookmark: where the SoulDiary was last closed.
  useEffect(() => {
    soulApi
      .getBookmark()
      .then(setBookmark)
      .catch(() => setBookmark(null));
  }, []);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      if (query.trim()) {
        const results = await soulApi.search(query.trim());
        setBooks(results.books);
      } else {
        setBooks(await soulApi.listBooks(sort, showArchived));
      }
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not load your library.");
    } finally {
      setLoading(false);
    }
  }, [sort, showArchived, query]);

  useEffect(() => {
    const t = setTimeout(load, query ? 250 : 0); // debounce search
    return () => clearTimeout(t);
  }, [load, query]);

  const create = async (title: string) => {
    const t = title.trim();
    if (!t) return;
    const book = await soulApi.createBook({ title: t });
    setNewTitle("");
    router.push(`/soulbooks/${book.id}`);
  };

  const rename = async (book: SoulBook) => {
    const next = window.prompt("Rename SoulBook", book.title);
    if (next && next.trim() && next.trim() !== book.title) {
      await soulApi.updateBook(book.id, { title: next.trim() });
      load();
    }
  };

  const archive = async (book: SoulBook) => {
    await (book.is_archived ? soulApi.restoreBook(book.id) : soulApi.archiveBook(book.id));
    load();
  };

  const remove = async (book: SoulBook) => {
    if (window.confirm(`Delete "${book.title}"? You can rebuild it later.`)) {
      await soulApi.deleteBook(book.id);
      load();
    }
  };

  return (
    <main className="mx-auto min-h-screen max-w-5xl px-6 py-10">
      <motion.header
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        className="mb-8"
      >
        <h1 className="bg-gradient-to-r from-soul-primary to-soul-accent bg-clip-text text-4xl font-extrabold text-transparent">
          Soul Library
        </h1>
        <p className="mt-2 text-soul-muted">Your SoulBooks — every story you keep.</p>
      </motion.header>

      {/* Reopen to the bookmarked page */}
      {bookmark && (
        <motion.button
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.15 }}
          onClick={() =>
            router.push(
              `/soulbooks/${bookmark.book_id}/chapters/${bookmark.chapter_id}/pages/${bookmark.page_id}`,
            )
          }
          className="mb-6 flex w-full items-center gap-4 rounded-2xl border border-soul-primary/30 bg-soul-surface/70 p-4 text-left shadow-lg transition-colors hover:border-soul-primary"
        >
          <span className="h-10 w-2.5 shrink-0 rounded-b-md bg-gradient-to-b from-soul-primary to-soul-accent" aria-hidden />
          <span>
            <span className="block text-sm font-semibold text-soul-accent">
              Continue your story — {bookmark.book_title}
            </span>
            <span className="block text-xs text-soul-muted">
              {bookmark.chapter_title} · {bookmark.page_title} · your ribbon is keeping the page
            </span>
          </span>
        </motion.button>
      )}

      {/* Create */}
      <div className="mb-6 flex flex-wrap items-center gap-3">
        <input
          aria-label="New SoulBook title"
          value={newTitle}
          onChange={(e) => setNewTitle(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && create(newTitle)}
          placeholder="Name a new SoulBook…"
          className="flex-1 rounded-lg border border-soul-primary/30 bg-soul-surface px-4 py-2.5 text-soul-accent outline-none focus:border-soul-primary"
        />
        <PrimaryButton onClick={() => create(newTitle)} disabled={!newTitle.trim()}>
          Create SoulBook
        </PrimaryButton>
      </div>

      <div className="mb-6 flex flex-wrap gap-2">
        {EXAMPLES.map((ex) => (
          <button
            key={ex}
            onClick={() => create(ex)}
            className="rounded-full border border-soul-primary/30 px-3 py-1 text-sm text-soul-muted transition-colors hover:border-soul-primary hover:text-soul-accent"
          >
            + {ex}
          </button>
        ))}
      </div>

      {/* Toolbar */}
      <div className="mb-6 flex flex-wrap items-center gap-3">
        <input
          aria-label="Search SoulBooks"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Search…"
          className="flex-1 rounded-lg border border-soul-primary/30 bg-soul-surface px-4 py-2 text-soul-accent outline-none focus:border-soul-primary"
        />
        <select
          aria-label="Sort SoulBooks"
          value={sort}
          onChange={(e) => setSort(e.target.value as SortOption)}
          disabled={!!query}
          className="rounded-lg border border-soul-primary/30 bg-soul-surface px-3 py-2 text-soul-accent"
        >
          {SORTS.map((s) => (
            <option key={s.value} value={s.value}>
              {s.label}
            </option>
          ))}
        </select>
        <label className="flex items-center gap-2 text-sm text-soul-muted">
          <input
            type="checkbox"
            checked={showArchived}
            onChange={(e) => setShowArchived(e.target.checked)}
            className="accent-soul-primary"
          />
          Show archived
        </label>
      </div>

      {error && <p className="mb-4 text-red-400">{error}</p>}
      {loading && <p className="text-soul-muted">Opening your library…</p>}

      {!loading && books.length === 0 && (
        <p className="text-soul-muted">
          {query ? "No SoulBooks match your search." : "No SoulBooks yet — create your first above."}
        </p>
      )}

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
        <AnimatePresence>
          {books.map((book) => (
            <motion.div
              key={book.id}
              layout
              initial={{ opacity: 0, scale: 0.96 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.96 }}
              whileHover={{ y: -4 }}
              className="relative flex flex-col justify-between overflow-hidden rounded-2xl border border-soul-primary/20 bg-soul-surface p-5 shadow-lg"
            >
              {bookmark?.book_id === book.id && (
                <span
                  aria-label="Ribbon bookmark"
                  className="absolute right-5 top-0 h-9 w-2.5 rounded-b-md bg-gradient-to-b from-soul-primary to-soul-accent shadow"
                />
              )}
              <button onClick={() => router.push(`/soulbooks/${book.id}`)} className="text-left">
                <h3 className="text-xl font-semibold text-soul-accent">{book.title}</h3>
                <p className="mt-1 text-sm text-soul-muted">
                  {book.chapter_count} chapter{book.chapter_count === 1 ? "" : "s"}
                  {book.is_archived ? " · Archived" : ""}
                </p>
              </button>
              <div className="mt-4 flex flex-wrap gap-3 text-sm">
                <button onClick={() => router.push(`/soulbooks/${book.id}`)} className="text-soul-primary hover:text-soul-accent">
                  Open
                </button>
                <button onClick={() => rename(book)} className="text-soul-muted hover:text-soul-accent">
                  Rename
                </button>
                <button onClick={() => archive(book)} className="text-soul-muted hover:text-soul-accent">
                  {book.is_archived ? "Restore" : "Archive"}
                </button>
                <button onClick={() => remove(book)} className="text-soul-muted hover:text-red-400">
                  Delete
                </button>
              </div>
            </motion.div>
          ))}
        </AnimatePresence>
      </div>
    </main>
  );
}
