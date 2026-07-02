import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

// Mock the router and API before importing the component.
vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: vi.fn(), replace: vi.fn() }),
}));

vi.mock("@/lib/api", () => ({
  ApiError: class ApiError extends Error {},
  authApi: {
    getAgreement: vi.fn().mockResolvedValue({
      version: "2026-06-30",
      checkbox_label: "I have read and agree...",
      content: "Mini SoulSpace User Acknowledgment content",
    }),
    register: vi.fn().mockResolvedValue({
      user: { display_name: "Aria Moon" },
      preferences: {},
    }),
  },
}));

import { RegisterForm } from "./RegisterForm";

async function fillValidFields() {
  const user = userEvent.setup();
  await user.type(screen.getByLabelText("Display Name"), "Aria Moon");
  await user.type(screen.getByLabelText("Email"), "aria@example.com");
  await user.type(screen.getByLabelText("Password", { exact: true }), "StrongPass123");
  await user.type(screen.getByLabelText("Confirm Password"), "StrongPass123");
  fireEvent.change(screen.getByLabelText("Date of Birth"), {
    target: { value: "1995-05-20" },
  });
  await user.type(screen.getByLabelText("State / Province / Region"), "California");
}

describe("RegisterForm — Create Account gating", () => {
  beforeEach(() => vi.clearAllMocks());

  it("keeps Create Account disabled until the form is valid AND the agreement is accepted", async () => {
    const user = userEvent.setup();
    render(<RegisterForm />);

    const createBtn = screen.getByRole("button", { name: /create account/i });
    expect(createBtn).toBeDisabled();

    await fillValidFields();

    // All fields valid but agreement not yet accepted -> still disabled.
    expect(createBtn).toBeDisabled();

    // Open the mandatory agreement modal and accept it.
    await user.click(screen.getByRole("button", { name: /i have read and agree/i }));
    const agreeBtn = await screen.findByRole("button", { name: /agree & continue/i });
    await user.click(agreeBtn);

    // Now enabled.
    await waitFor(() => expect(createBtn).toBeEnabled());
  });

  it("marks the timezone as manually set after an override", async () => {
    render(<RegisterForm />);
    expect(await screen.findByText(/auto-detected/i)).toBeInTheDocument();

    fireEvent.change(screen.getByLabelText("Timezone"), {
      target: { value: "Europe/Paris" },
    });
    expect(await screen.findByText(/manually set/i)).toBeInTheDocument();
  });
});
