import type { Metadata } from "next";
import { LoginForm } from "@/features/auth/LoginForm";

export const metadata: Metadata = {
  title: "Log in — Mini SoulSpace",
};

export default function LoginPage() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center bg-gradient-to-b from-soul-bg to-soul-surface px-6 py-12">
      <div className="mb-8 text-center">
        <h1 className="bg-gradient-to-r from-soul-primary to-soul-accent bg-clip-text text-4xl font-extrabold text-transparent">
          Welcome back
        </h1>
        <p className="mt-2 text-soul-muted">Your SoulDiary is waiting.</p>
      </div>

      <LoginForm />
    </main>
  );
}
