import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

const push = vi.fn();
vi.mock("next/navigation", () => ({
  useRouter: () => ({ push }),
  usePathname: () => "/soulbooks/b1/chapters/c1/pages/p1",
}));

const getPage = vi.fn();
const updatePage = vi.fn();
const autosavePage = vi.fn();
vi.mock("@/lib/api", () => ({
  ApiError: class ApiError extends Error {},
  soulApi: {
    getPage: (...a: unknown[]) => getPage(...a),
    updatePage: (...a: unknown[]) => updatePage(...a),
    autosavePage: (...a: unknown[]) => autosavePage(...a),
  },
}));

import { WritingPage } from "./WritingPage";

const page = {
  id: "p1",
  book_id: "b1",
  chapter_id: "c1",
  title: "Day One",
  content: "Dear Diary...\n\n",
  page_number: 1,
  content_format: "markdown" as const,
  timezone: null,
  word_count: 2,
  character_count: 15,
  is_deleted: false,
  created_at: "2026-07-01T00:00:00Z",
  updated_at: "2026-07-01T00:00:00Z",
};

describe("WritingPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    getPage.mockResolvedValue(page);
    updatePage.mockResolvedValue({ ...page, updated_at: "2026-07-01T01:00:00Z" });
    autosavePage.mockResolvedValue({
      id: "p1",
      updated_at: "2026-07-01T01:00:00Z",
      word_count: 3,
      character_count: 20,
      status: "saved",
    });
  });

  it("renders the page starting with 'Dear Diary...' and Saved status", async () => {
    render(<WritingPage />);
    const area = (await screen.findByLabelText("Writing area")) as HTMLTextAreaElement;
    expect(area.value.startsWith("Dear Diary...")).toBe(true);
    expect(screen.getByText("Saved")).toBeInTheDocument();
  });

  it("shows 'Unsaved changes' when typing, then auto-saves", async () => {
    const user = userEvent.setup();
    render(<WritingPage />);
    const area = await screen.findByLabelText("Writing area");
    await user.type(area, " more");
    expect(screen.getByText("Unsaved changes")).toBeInTheDocument();
    await waitFor(() => expect(autosavePage).toHaveBeenCalled(), { timeout: 3000 });
  });

  it("manual Save calls updatePage", async () => {
    const user = userEvent.setup();
    render(<WritingPage />);
    await screen.findByLabelText("Writing area");
    fireEvent.change(screen.getByLabelText("Writing area"), {
      target: { value: "Dear Diary...\n\nToday was calm." },
    });
    await user.click(screen.getByRole("button", { name: /^save$/i }));
    await waitFor(() => expect(updatePage).toHaveBeenCalled());
  });
});
