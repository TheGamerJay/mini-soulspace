"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { useForm } from "react-hook-form";

import { FormField, inputClass } from "@/components/FormField";
import { PasswordInput } from "@/components/PasswordInput";
import { PrimaryButton } from "@/components/PrimaryButton";
import { loginSchema, type LoginFormValues } from "@/features/auth/validation";
import { ApiError } from "@/lib/api";
import { useAuthStore } from "@/stores/authStore";

export function LoginForm() {
  const router = useRouter();
  const login = useAuthStore((s) => s.login);
  const [serverError, setServerError] = useState<string | null>(null);

  const {
    register,
    handleSubmit,
    formState: { errors, isValid, isSubmitting },
  } = useForm<LoginFormValues>({
    resolver: zodResolver(loginSchema),
    mode: "onChange",
  });

  const onSubmit = async (values: LoginFormValues) => {
    setServerError(null);
    try {
      await login(values.email, values.password);
      router.push("/home");
    } catch (err) {
      setServerError(
        err instanceof ApiError ? err.message : "Something went wrong.",
      );
    }
  };

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="flex w-full max-w-sm flex-col gap-4">
      <FormField label="Email" htmlFor="login_email" error={errors.email?.message}>
        <input id="login_email" type="email" className={inputClass} {...register("email")} />
      </FormField>

      <FormField label="Password" htmlFor="login_password" error={errors.password?.message}>
        <PasswordInput id="login_password" autoComplete="current-password" {...register("password")} />
      </FormField>

      {serverError && <p className="text-sm text-red-400">{serverError}</p>}

      <PrimaryButton type="submit" disabled={!isValid || isSubmitting} className="mt-2 w-full">
        {isSubmitting ? "Signing in…" : "Log In"}
      </PrimaryButton>

      <p className="text-center text-sm text-soul-muted">
        New here?{" "}
        <Link href="/register" className="text-soul-primary hover:text-soul-accent">
          Create an account
        </Link>
      </p>
    </form>
  );
}
