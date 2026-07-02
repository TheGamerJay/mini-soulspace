"use client";

import Link from "next/link";
import { useState } from "react";

import { AuthGuard } from "@/components/AuthGuard";
import { FormField, inputClass } from "@/components/FormField";
import { PrimaryButton } from "@/components/PrimaryButton";
import { authApi, ApiError } from "@/lib/api";
import { COUNTRIES, LANGUAGES } from "@/lib/options";
import { listTimezones } from "@/lib/timezone";
import { useAuthStore } from "@/stores/authStore";

function ProfileContent() {
  const user = useAuthStore((s) => s.user)!;
  const setState = useAuthStore.setState;

  const [region, setRegion] = useState(user.region);
  const [country, setCountry] = useState(user.country);
  const [timezone, setTimezone] = useState(user.timezone);
  const [language, setLanguage] = useState(user.preferred_language);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  const save = async () => {
    setSaving(true);
    setMessage(null);
    setError(null);
    try {
      const updated = await authApi.updateProfile({
        region,
        country,
        timezone,
        preferred_language: language,
      });
      setState({ user: updated });
      setMessage("Profile saved.");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not save profile.");
    } finally {
      setSaving(false);
    }
  };

  return (
    <main className="mx-auto flex min-h-screen max-w-lg flex-col gap-4 px-6 py-12">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold text-soul-accent">Your profile</h1>
        <Link href="/home" className="text-sm text-soul-primary hover:text-soul-accent">
          ← Home
        </Link>
      </div>

      <FormField label="Display Name">
        <input className={inputClass} value={user.display_name} disabled />
      </FormField>
      <FormField label="Email">
        <input className={inputClass} value={user.email} disabled />
      </FormField>

      <FormField label="State / Province / Region">
        <input className={inputClass} value={region} onChange={(e) => setRegion(e.target.value)} />
      </FormField>

      <FormField label="Country">
        <select className={inputClass} value={country} onChange={(e) => setCountry(e.target.value)}>
          {COUNTRIES.map((c) => (
            <option key={c.value} value={c.value}>
              {c.label}
            </option>
          ))}
        </select>
      </FormField>

      <FormField label="Timezone">
        <select className={inputClass} value={timezone} onChange={(e) => setTimezone(e.target.value)}>
          {listTimezones().map((tz) => (
            <option key={tz} value={tz}>
              {tz}
            </option>
          ))}
        </select>
      </FormField>

      <FormField label="Preferred Language">
        <select className={inputClass} value={language} onChange={(e) => setLanguage(e.target.value)}>
          {LANGUAGES.map((l) => (
            <option key={l.value} value={l.value}>
              {l.label}
            </option>
          ))}
        </select>
      </FormField>

      {message && <p className="text-sm text-green-400">{message}</p>}
      {error && <p className="text-sm text-red-400">{error}</p>}

      <PrimaryButton onClick={save} disabled={saving} className="mt-2 w-full">
        {saving ? "Saving…" : "Save changes"}
      </PrimaryButton>
    </main>
  );
}

export default function ProfilePage() {
  return (
    <AuthGuard>
      <ProfileContent />
    </AuthGuard>
  );
}
