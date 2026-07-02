import type { Metadata } from "next";
import Link from "next/link";
import { RegisterForm } from "@/features/auth/RegisterForm";

export const metadata: Metadata = {
  title: "Create your SoulSpace",
};

export default function RegisterPage() {
  return (
    <main className="flex min-h-screen flex-col items-center bg-gradient-to-b from-soul-bg to-soul-surface px-6 py-12">
      <div className="mb-8 text-center">
        <h1 className="bg-gradient-to-r from-soul-primary to-soul-accent bg-clip-text text-4xl font-extrabold text-transparent">
          Create your SoulSpace
        </h1>
        <p className="mt-2 text-soul-muted">Begin your story — a diary that talks back.</p>
      </div>

      <RegisterForm />

      <p className="mt-6 text-sm text-soul-muted">
        Already have an account?{" "}
        <Link href="/login" className="text-soul-primary hover:text-soul-accent">
          Log in
        </Link>
      </p>
    </main>
  );
}
