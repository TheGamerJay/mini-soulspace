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
