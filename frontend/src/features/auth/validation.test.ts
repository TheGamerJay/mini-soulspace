import { describe, expect, it } from "vitest";
import { registerSchema, loginSchema } from "./validation";

const base = {
  display_name: "Aria Moon",
  email: "aria@example.com",
  password: "StrongPass123",
  confirm_password: "StrongPass123",
  date_of_birth: "1995-05-20",
  country: "US",
  region: "California",
  timezone: "America/Los_Angeles",
  preferred_language: "en",
  agreement_accepted: true,
};

describe("registerSchema", () => {
  it("accepts a fully valid payload", () => {
    expect(registerSchema.safeParse(base).success).toBe(true);
  });

  it("rejects a weak password", () => {
    const r = registerSchema.safeParse({ ...base, password: "weak", confirm_password: "weak" });
    expect(r.success).toBe(false);
  });

  it("rejects mismatched passwords", () => {
    const r = registerSchema.safeParse({ ...base, confirm_password: "Different123" });
    expect(r.success).toBe(false);
  });

  it("rejects when the agreement is not accepted", () => {
    const r = registerSchema.safeParse({ ...base, agreement_accepted: false });
    expect(r.success).toBe(false);
  });

  it("requires a region", () => {
    const r = registerSchema.safeParse({ ...base, region: "" });
    expect(r.success).toBe(false);
  });
});

describe("loginSchema", () => {
  it("accepts valid credentials", () => {
    expect(loginSchema.safeParse({ email: "a@b.com", password: "x" }).success).toBe(true);
  });
  it("rejects an invalid email", () => {
    expect(loginSchema.safeParse({ email: "nope", password: "x" }).success).toBe(false);
  });
});
