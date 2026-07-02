"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { useForm } from "react-hook-form";

import { AcknowledgmentModal } from "@/components/AcknowledgmentModal";
import { FormField, inputClass } from "@/components/FormField";
import { PasswordInput } from "@/components/PasswordInput";
import { PrimaryButton } from "@/components/PrimaryButton";
import { registerSchema, type RegisterFormValues } from "@/features/auth/validation";
import { ApiError } from "@/lib/api";
import { COUNTRIES, LANGUAGES } from "@/lib/options";
import { detectTimezone, listTimezones } from "@/lib/timezone";
import { useAuthStore } from "@/stores/authStore";

const AGREEMENT_LABEL =
  "I have read and agree to the Mini SoulSpace User Acknowledgment, Terms of Service and Privacy Policy.";

export function RegisterForm() {
  const router = useRouter();
  const registerUser = useAuthStore((s) => s.register);

  const [modalOpen, setModalOpen] = useState(false);
  const [agreementVersion, setAgreementVersion] = useState("");
  const [tzAutoDetected, setTzAutoDetected] = useState(true);
  const [timezones, setTimezones] = useState<string[]>([]);
  const [serverError, setServerError] = useState<string | null>(null);

  const {
    register,
    handleSubmit,
    setValue,
    watch,
    formState: { errors, isValid, isSubmitting },
  } = useForm<RegisterFormValues>({
    resolver: zodResolver(registerSchema),
    mode: "onChange",
    defaultValues: {
      preferred_language: "en",
      country: "US",
      agreement_accepted: false as unknown as true,
    },
  });

  // Auto-detect timezone on mount (manual override allowed below).
  useEffect(() => {
    setTimezones(listTimezones());
    const detected = detectTimezone();
    setValue("timezone", detected, { shouldValidate: true });
  }, [setValue]);

  const agreementAccepted = watch("agreement_accepted");

  const onSubmit = async (values: RegisterFormValues) => {
    setServerError(null);
    try {
      await registerUser({
        ...values,
        timezone_auto_detected: tzAutoDetected,
        agreement_version: agreementVersion,
      });
      router.push("/home");
    } catch (err) {
      setServerError(err instanceof ApiError ? err.message : "Something went wrong.");
    }
  };

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="flex w-full max-w-lg flex-col gap-4">
      <FormField label="Display Name" htmlFor="display_name" error={errors.display_name?.message}>
        <input id="display_name" className={inputClass} {...register("display_name")} />
      </FormField>

      <FormField label="Email" htmlFor="email" error={errors.email?.message}>
        <input id="email" type="email" className={inputClass} {...register("email")} />
      </FormField>

      <FormField label="Password" htmlFor="password" error={errors.password?.message}>
        <PasswordInput id="password" autoComplete="new-password" {...register("password")} />
      </FormField>

      <FormField
        label="Confirm Password"
        htmlFor="confirm_password"
        error={errors.confirm_password?.message}
      >
        <PasswordInput
          id="confirm_password"
          autoComplete="new-password"
          {...register("confirm_password")}
        />
      </FormField>

      <FormField label="Date of Birth" htmlFor="date_of_birth" error={errors.date_of_birth?.message}>
        <input id="date_of_birth" type="date" className={inputClass} {...register("date_of_birth")} />
      </FormField>

      <FormField label="Country" htmlFor="country" error={errors.country?.message}>
        <select id="country" className={inputClass} {...register("country")}>
          {COUNTRIES.map((c) => (
            <option key={c.value} value={c.value}>
              {c.label}
            </option>
          ))}
        </select>
      </FormField>

      <FormField
        label="State / Province / Region"
        htmlFor="region"
        error={errors.region?.message}
      >
        <input id="region" className={inputClass} {...register("region")} />
      </FormField>

      <FormField label="Timezone" htmlFor="timezone" error={errors.timezone?.message}>
        <select
          id="timezone"
          className={inputClass}
          {...register("timezone", {
            onChange: () => setTzAutoDetected(false),
          })}
        >
          {timezones.map((tz) => (
            <option key={tz} value={tz}>
              {tz}
            </option>
          ))}
        </select>
        <p className="text-xs text-soul-muted">
          {tzAutoDetected ? "Auto-detected — change it if it's wrong." : "Manually set."}
        </p>
      </FormField>

      <FormField
        label="Preferred Language"
        htmlFor="preferred_language"
        error={errors.preferred_language?.message}
      >
        <select id="preferred_language" className={inputClass} {...register("preferred_language")}>
          {LANGUAGES.map((l) => (
            <option key={l.value} value={l.value}>
              {l.label}
            </option>
          ))}
        </select>
      </FormField>

      {/* Mandatory combined agreement */}
      <div className="flex items-start gap-3 rounded-lg border border-soul-primary/20 p-3">
        <input
          type="checkbox"
          aria-label="Accept the agreement"
          checked={!!agreementAccepted}
          readOnly
          onClick={(e) => {
            e.preventDefault();
            if (agreementAccepted) {
              setValue("agreement_accepted", false as unknown as true, {
                shouldValidate: true,
              });
            } else {
              setModalOpen(true);
            }
          }}
          className="mt-1 h-5 w-5 shrink-0 cursor-pointer accent-soul-primary"
        />
        <button
          type="button"
          onClick={() => setModalOpen(true)}
          className="text-left text-sm text-soul-muted underline decoration-soul-primary/50 underline-offset-2 hover:text-soul-accent"
        >
          {AGREEMENT_LABEL}
        </button>
      </div>
      {errors.agreement_accepted && (
        <p className="text-sm text-red-400">{errors.agreement_accepted.message}</p>
      )}

      {serverError && <p className="text-sm text-red-400">{serverError}</p>}

      <PrimaryButton type="submit" disabled={!isValid || isSubmitting} className="mt-2 w-full">
        {isSubmitting ? "Creating…" : "Create Account"}
      </PrimaryButton>

      <AcknowledgmentModal
        open={modalOpen}
        onClose={() => setModalOpen(false)}
        onAgree={(version) => {
          setAgreementVersion(version);
          setValue("agreement_accepted", true, { shouldValidate: true });
          setModalOpen(false);
        }}
      />
    </form>
  );
}
