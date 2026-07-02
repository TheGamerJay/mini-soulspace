import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

const push = vi.fn();
const replace = vi.fn();
vi.mock("next/navigation", () => ({
  useRouter: () => ({ push, replace }),
}));

import HomePage from "./page";
import { useAuthStore } from "@/stores/authStore";

describe("Home screen", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    // Pretend we're logged in so the AuthGuard renders the Home content.
    useAuthStore.setState({
      status: "authenticated",
      user: {
        id: "u1",
        email: "a@example.com",
        display_name: "Aria Moon",
        date_of_birth: "1995-05-20",
        country: "US",
        region: "California",
        timezone: "America/Los_Angeles",
        preferred_language: "en",
        is_active: true,
        is_verified: false,
        last_login_at: null,
        created_at: "2026-07-01T00:00:00Z",
      },
      preferences: null,
    });
  });

  it("greets the user and 'Open My SoulDiary' goes to the Soul Library", async () => {
    const user = userEvent.setup();
    render(<HomePage />);
    expect(screen.getByText(/welcome back, aria/i)).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: /open my souldiary/i }));
    expect(push).toHaveBeenCalledWith("/soul-library");
  });
});
