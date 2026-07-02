/**
 * Typed API client for the Mini SoulSpace backend.
 *
 * Same-origin in the unified deployment (empty base → "/api"). All auth uses
 * httpOnly cookies, so every request sends credentials.
 */

import type {
  Agreement,
  AuthResponse,
  PageSaveResult,
  RegisterPayload,
  SearchResults,
  SoulBook,
  SoulChapter,
  SoulPage,
  SortOption,
  User,
} from "@/lib/types";

export const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "";
export const API_URL = `${API_BASE}/api`;

export class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
    this.name = "ApiError";
  }
}

function extractDetail(status: number, data: unknown): string {
  if (data && typeof data === "object" && "detail" in data) {
    const detail = (data as { detail: unknown }).detail;
    if (typeof detail === "string") return detail;
    if (Array.isArray(detail) && detail.length > 0) {
      const first = detail[0] as { msg?: string };
      if (first?.msg) return first.msg.replace(/^Value error,\s*/, "");
    }
  }
  return `Request failed (${status})`;
}

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const res = await fetch(`${API_URL}${path}`, {
    credentials: "include",
    headers: { "Content-Type": "application/json", ...(init.headers ?? {}) },
    ...init,
  });

  let data: unknown = null;
  const text = await res.text();
  if (text) {
    try {
      data = JSON.parse(text);
    } catch {
      data = text;
    }
  }

  if (!res.ok) {
    throw new ApiError(res.status, extractDetail(res.status, data));
  }
  return data as T;
}

export const authApi = {
  getAgreement: () => request<Agreement>("/legal/agreement"),
  register: (payload: RegisterPayload) =>
    request<AuthResponse>("/auth/register", {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  login: (email: string, password: string) =>
    request<AuthResponse>("/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    }),
  logout: () => request<{ message: string }>("/auth/logout", { method: "POST" }),
  me: () => request<AuthResponse>("/auth/me"),
  updateProfile: (patch: Partial<User>) =>
    request<User>("/users/me", { method: "PATCH", body: JSON.stringify(patch) }),
};

const base = "/soulbooks";

export const soulApi = {
  // Books
  listBooks: (sort: SortOption = "recently_opened", includeArchived = false) =>
    request<SoulBook[]>(`${base}?sort=${sort}&include_archived=${includeArchived}`),
  createBook: (data: { title: string; description?: string }) =>
    request<SoulBook>(base, { method: "POST", body: JSON.stringify(data) }),
  getBook: (bookId: string) => request<SoulBook>(`${base}/${bookId}`),
  updateBook: (bookId: string, patch: { title?: string; description?: string }) =>
    request<SoulBook>(`${base}/${bookId}`, { method: "PATCH", body: JSON.stringify(patch) }),
  deleteBook: (bookId: string) =>
    request<void>(`${base}/${bookId}`, { method: "DELETE" }),
  archiveBook: (bookId: string) =>
    request<SoulBook>(`${base}/${bookId}/archive`, { method: "POST" }),
  restoreBook: (bookId: string) =>
    request<SoulBook>(`${base}/${bookId}/restore`, { method: "POST" }),

  // Chapters
  listChapters: (bookId: string) =>
    request<SoulChapter[]>(`${base}/${bookId}/chapters`),
  createChapter: (bookId: string, data: { title: string }) =>
    request<SoulChapter>(`${base}/${bookId}/chapters`, {
      method: "POST",
      body: JSON.stringify(data),
    }),
  getChapter: (bookId: string, chapterId: string) =>
    request<SoulChapter>(`${base}/${bookId}/chapters/${chapterId}`),
  updateChapter: (bookId: string, chapterId: string, patch: { title?: string }) =>
    request<SoulChapter>(`${base}/${bookId}/chapters/${chapterId}`, {
      method: "PATCH",
      body: JSON.stringify(patch),
    }),
  deleteChapter: (bookId: string, chapterId: string) =>
    request<void>(`${base}/${bookId}/chapters/${chapterId}`, { method: "DELETE" }),

  // Pages
  listPages: (bookId: string, chapterId: string) =>
    request<SoulPage[]>(`${base}/${bookId}/chapters/${chapterId}/pages`),
  createPage: (bookId: string, chapterId: string, data: { title: string }) =>
    request<SoulPage>(`${base}/${bookId}/chapters/${chapterId}/pages`, {
      method: "POST",
      body: JSON.stringify(data),
    }),
  getPage: (bookId: string, chapterId: string, pageId: string) =>
    request<SoulPage>(`${base}/${bookId}/chapters/${chapterId}/pages/${pageId}`),
  updatePage: (
    bookId: string,
    chapterId: string,
    pageId: string,
    patch: { title?: string; content?: string },
  ) =>
    request<SoulPage>(`${base}/${bookId}/chapters/${chapterId}/pages/${pageId}`, {
      method: "PATCH",
      body: JSON.stringify(patch),
    }),
  autosavePage: (
    bookId: string,
    chapterId: string,
    pageId: string,
    patch: { title?: string; content?: string },
  ) =>
    request<PageSaveResult>(
      `${base}/${bookId}/chapters/${chapterId}/pages/${pageId}/autosave`,
      { method: "PATCH", body: JSON.stringify(patch) },
    ),
  deletePage: (bookId: string, chapterId: string, pageId: string) =>
    request<void>(`${base}/${bookId}/chapters/${chapterId}/pages/${pageId}`, {
      method: "DELETE",
    }),

  // Search
  search: (q: string) =>
    request<SearchResults>(`${base}/search?q=${encodeURIComponent(q)}`),
};
