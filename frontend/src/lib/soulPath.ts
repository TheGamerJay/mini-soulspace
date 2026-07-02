/** Parse SoulBook ids from the live URL (works with the static-export SPA fallback). */
export function parseSoulPath(pathname: string): {
  bookId: string | null;
  chapterId: string | null;
  pageId: string | null;
} {
  // /soulbooks/<bookId>/chapters/<chapterId>/pages/<pageId>
  const parts = pathname.split("/").filter(Boolean);
  return {
    bookId: parts[1] ?? null,
    chapterId: parts[3] ?? null,
    pageId: parts[5] ?? null,
  };
}
