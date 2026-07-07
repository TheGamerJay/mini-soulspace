"use client";

import { AnimatePresence, motion } from "framer-motion";
import { useRouter } from "next/navigation";
import { useCallback, useEffect, useState } from "react";

import { PrimaryButton } from "@/components/PrimaryButton";
import { ThemeSwitcher } from "@/components/ThemeSwitcher";
import { ApiError, soulApi } from "@/lib/api";
import type { Bookmark, SoulBook, SoulBookPatch, SortOption } from "@/lib/types";

const SORTS: { value: SortOption; label: string }[] = [
  { value: "recently_opened", label: "Recently Opened" },
  { value: "recently_updated", label: "Recently Updated" },
  { value: "alphabetical", label: "Alphabetical" },
  { value: "newest", label: "Newest" },
  { value: "oldest", label: "Oldest" },
];

// Default shelf: every example feels like a distinct keepsake.
const EXAMPLES: { title: string; color: string; icon: string }[] = [
  { title: "Daily Journal", color: "#7a5230", icon: "📔" },
  { title: "Dream Journal", color: "#31589e", icon: "🌙" },
  { title: "Travel Journal", color: "#2e7d4f", icon: "🧭" },
  { title: "Project Notebook", color: "#5a5f6a", icon: "🗂️" },
  { title: "Creative Journal", color: "#6d4b9e", icon: "🎨" },
  { title: "Prayer Journal", color: "#8a6d3b", icon: "🕊️" },
  { title: "Gratitude Journal", color: "#a3542f", icon: "🌻" },
  { title: "Health Journal", color: "#2f7d7d", icon: "🌿" },
  { title: "Learning Journal", color: "#455a8f", icon: "📚" },
];

const COVER_COLORS = ["#6d5bd0", "#31589e", "#7a5230", "#2e7d4f", "#5a5f6a", "#6d4b9e", "#a3542f", "#2f7d7d"];
const RIBBON_COLORS = ["#e0b64c", "#c0392b", "#2e7d4f", "#31589e", "#b7a6ff", "#e88fb1"];
const ICONS = ["📔", "🌙", "🧭", "🗂️", "🎨", "🕊️", "🌻", "🌿", "📚", "💜", "✨", "🕯️"];
// Cover materials — vintage/fantasy/etc. are future-ready cover styles.
const MATERIALS = ["leather", "cloth", "hardcover", "vintage", "modern"];

function isRecent(iso: string | null): boolean {
  if (!iso) return false;
  return Date.now() - new Date(iso).getTime() < 24 * 60 * 60 * 1000;
}

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
  const [customizing, setCustomizing] = useState<SoulBook | null>(null);

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

  const create = async (title: string, extras?: { cover_color?: string; icon?: string }) => {
    const t = title.trim();
    if (!t) return;
    const book = await soulApi.createBook({ title: t, ...extras });
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

  const toggleFavorite = async (book: SoulBook) => {
    await soulApi.updateBook(book.id, { is_favorite: !book.is_favorite });
    load();
  };

  const saveCustomization = async (book: SoulBook, patch: SoulBookPatch) => {
    await soulApi.updateBook(book.id, patch);
    setCustomizing(null);
    load();
  };

  const active = books.filter((b) => !b.is_archived);
  const archived = books.filter((b) => b.is_archived);

  return (
    <main className="mx-auto min-h-screen max-w-5xl px-6 py-10">
      <motion.header
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        className="mb-8 flex flex-wrap items-end justify-between gap-4"
      >
        <div>
          <h1 className="bg-gradient-to-r from-soul-primary to-soul-accent bg-clip-text text-4xl font-extrabold text-transparent">
            Soul Library
          </h1>
          <p className="mt-2 text-soul-muted">Your SoulBooks — every story you keep.</p>
        </div>
        <ThemeSwitcher />
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
            key={ex.title}
            onClick={() => create(ex.title, { cover_color: ex.color, icon: ex.icon })}
            className="rounded-full border border-soul-primary/30 px-3 py-1 text-sm text-soul-muted transition-all hover:-translate-y-0.5 hover:border-soul-primary hover:text-soul-accent"
          >
            {ex.icon} {ex.title}
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

      <Shelf
        books={active}
        bookmark={bookmark}
        onOpen={(b) => router.push(`/soulbooks/${b.id}`)}
        onRename={rename}
        onArchive={archive}
        onRemove={remove}
        onFavorite={toggleFavorite}
        onCustomize={setCustomizing}
      />

      {showArchived && archived.length > 0 && (
        <>
          <h2 className="mb-3 mt-10 text-sm font-semibold uppercase tracking-wider text-soul-muted">
            Archived shelf
          </h2>
          <Shelf
            books={archived}
            bookmark={bookmark}
            dim
            onOpen={(b) => router.push(`/soulbooks/${b.id}`)}
            onRename={rename}
            onArchive={archive}
            onRemove={remove}
            onFavorite={toggleFavorite}
            onCustomize={setCustomizing}
          />
        </>
      )}

      {customizing && (
        <CustomizeDialog
          book={customizing}
          onClose={() => setCustomizing(null)}
          onSave={saveCustomization}
        />
      )}
    </main>
  );
}

function Shelf({
  books,
  bookmark,
  dim = false,
  onOpen,
  onRename,
  onArchive,
  onRemove,
  onFavorite,
  onCustomize,
}: {
  books: SoulBook[];
  bookmark: Bookmark | null;
  dim?: boolean;
  onOpen: (b: SoulBook) => void;
  onRename: (b: SoulBook) => void;
  onArchive: (b: SoulBook) => void;
  onRemove: (b: SoulBook) => void;
  onFavorite: (b: SoulBook) => void;
  onCustomize: (b: SoulBook) => void;
}) {
  if (books.length === 0) return null;
  return (
    <div className="relative">
      <div className="grid grid-cols-1 gap-4 pb-3 sm:grid-cols-2 lg:grid-cols-3">
        <AnimatePresence>
          {books.map((book) => (
            <motion.div
              key={book.id}
              layout
              initial={{ opacity: 0, scale: 0.96 }}
              animate={{ opacity: dim ? 0.7 : 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.96 }}
              whileHover={{ y: -5 }}
              transition={{ type: "spring", stiffness: 220, damping: 22 }}
              className={`relative flex flex-col justify-between overflow-hidden rounded-2xl border border-soul-primary/20 bg-soul-surface p-5 shadow-lg ${
                isRecent(book.last_opened_at) ? "ring-1 ring-soul-primary/40 shadow-soul-primary/20" : ""
              }`}
            >
              {/* Cover spine in the book's own color + material sheen */}
              <span
                aria-hidden
                style={{ backgroundColor: book.cover_color }}
                className={`absolute left-0 top-0 h-full w-2 ${
                  book.cover_material === "leather" ? "opacity-90" : "opacity-70"
                }`}
              />
              {bookmark?.book_id === book.id && (
                <span
                  aria-label="Ribbon bookmark"
                  style={{ backgroundColor: book.ribbon_color }}
                  className="absolute right-5 top-0 h-9 w-2.5 rounded-b-md shadow"
                />
              )}
              <button
                aria-label={book.is_favorite ? "Unpin favorite" : "Pin as favorite"}
                onClick={() => onFavorite(book)}
                className={`absolute right-4 top-3 text-lg transition-transform hover:scale-110 ${
                  book.is_favorite ? "" : "opacity-30 grayscale hover:opacity-70"
                }`}
              >
                ⭐
              </button>
              <button onClick={() => onOpen(book)} className="pl-3 text-left">
                <h3 className="text-xl font-semibold text-soul-accent">
                  <span aria-hidden className="mr-2">{book.icon}</span>
                  {book.title}
                </h3>
                <p className="mt-1 text-sm text-soul-muted">
                  {book.chapter_count} chapter{book.chapter_count === 1 ? "" : "s"}
                  {book.category ? ` · ${book.category}` : ""}
                  {book.is_archived ? " · Archived" : ""}
                  {isRecent(book.last_opened_at) ? " · recently opened" : ""}
                </p>
              </button>
              <div className="mt-4 flex flex-wrap gap-3 pl-3 text-sm">
                <button onClick={() => onOpen(book)} className="text-soul-primary hover:text-soul-accent">
                  Open
                </button>
                <button onClick={() => onRename(book)} className="text-soul-muted hover:text-soul-accent">
                  Rename
                </button>
                <button onClick={() => onCustomize(book)} className="text-soul-muted hover:text-soul-accent">
                  Customize
                </button>
                <button onClick={() => onArchive(book)} className="text-soul-muted hover:text-soul-accent">
                  {book.is_archived ? "Restore" : "Archive"}
                </button>
                <button onClick={() => onRemove(book)} className="text-soul-muted hover:text-red-400">
                  Delete
                </button>
              </div>
            </motion.div>
          ))}
        </AnimatePresence>
      </div>
      {/* Shelf depth */}
      <div aria-hidden className="h-2.5 rounded-full shadow-inner" style={{ background: "var(--soul-shelf)" }} />
    </div>
  );
}

function CustomizeDialog({
  book,
  onClose,
  onSave,
}: {
  book: SoulBook;
  onClose: () => void;
  onSave: (book: SoulBook, patch: SoulBookPatch) => void;
}) {
  const [color, setColor] = useState(book.cover_color);
  const [ribbon, setRibbon] = useState(book.ribbon_color);
  const [icon, setIcon] = useState(book.icon);
  const [material, setMaterial] = useState(book.cover_material);
  const [category, setCategory] = useState(book.category ?? "");
  const [description, setDescription] = useState(book.description ?? "");

  return (
    <div
      role="dialog"
      aria-label={`Customize ${book.title}`}
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4"
    >
      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        className="w-full max-w-md rounded-2xl border border-soul-primary/30 bg-soul-surface p-6 shadow-2xl"
      >
        <h2 className="mb-4 text-lg font-semibold text-soul-accent">
          <span aria-hidden className="mr-2">{icon}</span>Customize “{book.title}”
        </h2>

        <p className="mb-1 text-xs text-soul-muted">Cover color</p>
        <div className="mb-4 flex flex-wrap gap-2">
          {COVER_COLORS.map((c) => (
            <button
              key={c}
              aria-label={`Cover color ${c}`}
              onClick={() => setColor(c)}
              style={{ backgroundColor: c }}
              className={`h-7 w-7 rounded-full ${color === c ? "ring-2 ring-soul-accent ring-offset-2 ring-offset-soul-surface" : ""}`}
            />
          ))}
        </div>

        <p className="mb-1 text-xs text-soul-muted">Ribbon color</p>
        <div className="mb-4 flex flex-wrap gap-2">
          {RIBBON_COLORS.map((c) => (
            <button
              key={c}
              aria-label={`Ribbon color ${c}`}
              onClick={() => setRibbon(c)}
              style={{ backgroundColor: c }}
              className={`h-7 w-7 rounded-full ${ribbon === c ? "ring-2 ring-soul-accent ring-offset-2 ring-offset-soul-surface" : ""}`}
            />
          ))}
        </div>

        <p className="mb-1 text-xs text-soul-muted">Icon</p>
        <div className="mb-4 flex flex-wrap gap-1.5">
          {ICONS.map((i) => (
            <button
              key={i}
              aria-label={`Icon ${i}`}
              onClick={() => setIcon(i)}
              className={`rounded-lg px-1.5 py-0.5 text-xl ${icon === i ? "bg-soul-primary/30" : "hover:bg-soul-primary/15"}`}
            >
              {i}
            </button>
          ))}
        </div>

        <label className="mb-4 block text-xs text-soul-muted">
          Cover material
          <select
            value={material}
            onChange={(e) => setMaterial(e.target.value)}
            className="mt-1 w-full rounded-lg border border-soul-primary/30 bg-soul-bg px-3 py-2 text-soul-accent"
          >
            {MATERIALS.map((m) => (
              <option key={m} value={m}>
                {m}
              </option>
            ))}
          </select>
        </label>

        <label className="mb-3 block text-xs text-soul-muted">
          Category
          <input
            value={category}
            onChange={(e) => setCategory(e.target.value)}
            placeholder="e.g. Dreams, Gratitude, Projects…"
            className="mt-1 w-full rounded-lg border border-soul-primary/30 bg-soul-bg px-3 py-2 text-soul-accent outline-none focus:border-soul-primary"
          />
        </label>

        <label className="mb-5 block text-xs text-soul-muted">
          Description
          <input
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            placeholder="What lives in this book?"
            className="mt-1 w-full rounded-lg border border-soul-primary/30 bg-soul-bg px-3 py-2 text-soul-accent outline-none focus:border-soul-primary"
          />
        </label>

        <div className="flex justify-end gap-3">
          <button onClick={onClose} className="rounded-full px-4 py-1.5 text-sm text-soul-muted hover:text-soul-accent">
            Cancel
          </button>
          <button
            onClick={() =>
              onSave(book, {
                cover_color: color,
                ribbon_color: ribbon,
                icon,
                cover_material: material,
                category: category || undefined,
                description: description || undefined,
              })
            }
            className="rounded-full bg-soul-primary px-5 py-1.5 text-sm font-semibold text-white hover:bg-soul-accent"
          >
            Save keepsake
          </button>
        </div>
      </motion.div>
    </div>
  );
}
