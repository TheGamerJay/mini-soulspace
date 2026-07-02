import { z } from "zod";

/** Password policy — mirrors the backend rules exactly. */
export const passwordSchema = z
  .string()
  .min(9, "Password must be at least 9 characters.")
  .max(128, "Password must be at most 128 characters.")
  .regex(/[a-z]/, "Password must contain a lowercase letter.")
  .regex(/[A-Z]/, "Password must contain an uppercase letter.")
  .regex(/\d/, "Password must contain a number.");

export const registerSchema = z
  .object({
    display_name: z.string().trim().min(2, "Display name is too short.").max(50),
    email: z.string().email("Enter a valid email."),
    password: passwordSchema,
    confirm_password: z.string(),
    date_of_birth: z.string().min(1, "Date of birth is required."),
    country: z.string().min(2, "Select your country."),
    region: z.string().trim().min(1, "Enter your state / province / region."),
    timezone: z.string().min(1, "Timezone is required."),
    preferred_language: z.string().min(2, "Select a language."),
    // Single combined agreement checkbox — must be true.
    agreement_accepted: z.literal(true, {
      errorMap: () => ({ message: "You must accept the agreement." }),
    }),
  })
  .refine((data) => data.password === data.confirm_password, {
    path: ["confirm_password"],
    message: "Passwords do not match.",
  });

export type RegisterFormValues = z.infer<typeof registerSchema>;

export const loginSchema = z.object({
  email: z.string().email("Enter a valid email."),
  password: z.string().min(1, "Enter your password."),
});

export type LoginFormValues = z.infer<typeof loginSchema>;
