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
const closePage = vi.fn();
vi.mock("@/lib/api", () => ({
  ApiError: class ApiError extends Error {},
  soulApi: {
    getPage: (...a: unknown[]) => getPage(...a),
    updatePage: (...a: unknown[]) => updatePage(...a),
    autosavePage: (...a: unknown[]) => autosavePage(...a),
    closePage: (...a: unknown[]) => closePage(...a),
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

  it("Close SoulDiary shows the reflection beneath the page and the ribbon", async () => {
    closePage.mockResolvedValue({
      reflection: {
        trace_id: "t1",
        delivered: true,
        status: "delivered",
        text: "Thank you for writing this — it belongs in your story.",
        memory_updates: [],
        events: ["ConversationDelivered"],
        failure_reason: null,
        total_ms: 42,
      },
      bookmark: {
        book_id: "b1", chapter_id: "c1", page_id: "p1", cursor: 5,
        book_title: "B", chapter_title: "C", page_title: "P",
      },
    });
    const user = userEvent.setup();
    render(<WritingPage />);
    await screen.findByLabelText("Writing area");
    await user.click(screen.getByRole("button", { name: /close souldiary/i }));
    await waitFor(() => expect(closePage).toHaveBeenCalled());
    expect(
      await screen.findByText("Thank you for writing this — it belongs in your story."),
    ).toBeInTheDocument();
    expect(screen.getByLabelText("Ribbon bookmark")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /return to the shelf/i })).toBeInTheDocument();
  });

  it("failed reflection still keeps the page safe (gentle fallback)", async () => {
    closePage.mockRejectedValue(new Error("orchestra down"));
    const user = userEvent.setup();
    render(<WritingPage />);
    await screen.findByLabelText("Writing area");
    await user.click(screen.getByRole("button", { name: /close souldiary/i }));
    expect(await screen.findByText(/safely kept in your SoulDiary/i)).toBeInTheDocument();
  });
});
