/** Shared API types (mirror the backend Pydantic schemas). */

export interface User {
  id: string;
  email: string;
  display_name: string;
  date_of_birth: string;
  country: string;
  region: string;
  timezone: string;
  preferred_language: string;
  is_active: boolean;
  is_verified: boolean;
  last_login_at: string | null;
  created_at: string;
}

export interface UserPreferences {
  birthday_messages_enabled: boolean;
  milestone_messages_enabled: boolean;
  reflection_reminders_enabled: boolean;
  preferred_theme: string;
  timezone_auto_detected: boolean;
}

export interface AuthResponse {
  user: User;
  preferences: UserPreferences;
}

export interface Agreement {
  version: string;
  checkbox_label: string;
  content: string;
}

// ── SoulBook Engine ──────────────────────────────────────────────────────────
export interface SoulBook {
  id: string;
  title: string;
  description: string | null;
  cover_style: string;
  is_archived: boolean;
  is_deleted: boolean;
  created_at: string;
  updated_at: string;
  last_opened_at: string | null;
  chapter_count: number;
}

export interface SoulChapter {
  id: string;
  book_id: string;
  title: string;
  chapter_number: number;
  is_deleted: boolean;
  created_at: string;
  updated_at: string;
  last_opened_at: string | null;
  page_count: number;
}

export interface SoulPage {
  id: string;
  book_id: string;
  chapter_id: string;
  title: string;
  content: string;
  page_number: number;
  content_format: "plain_text" | "markdown";
  timezone: string | null;
  word_count: number;
  character_count: number;
  is_deleted: boolean;
  created_at: string;
  updated_at: string;
}

export interface PageSaveResult {
  id: string;
  updated_at: string;
  word_count: number;
  character_count: number;
  status: string;
}

export interface SearchResults {
  books: SoulBook[];
  pages: SoulPage[];
}

export type SortOption =
  | "recently_opened"
  | "recently_updated"
  | "alphabetical"
  | "newest"
  | "oldest";

export interface RegisterPayload {
  display_name: string;
  email: string;
  password: string;
  confirm_password: string;
  date_of_birth: string;
  country: string;
  region: string;
  timezone: string;
  preferred_language: string;
  timezone_auto_detected: boolean;
  agreement_accepted: boolean;
  agreement_version: string;
}
