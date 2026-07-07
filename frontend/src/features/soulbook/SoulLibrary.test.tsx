import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

const push = vi.fn();
vi.mock("next/navigation", () => ({
  useRouter: () => ({ push }),
  usePathname: () => "/soul-library",
}));

const listBooks = vi.fn();
const createBook = vi.fn();
const search = vi.fn();
vi.mock("@/lib/api", () => ({
  ApiError: class ApiError extends Error {},
  soulApi: {
    listBooks: (...a: unknown[]) => listBooks(...a),
    createBook: (...a: unknown[]) => createBook(...a),
    search: (...a: unknown[]) => search(...a),
    getBookmark: () => Promise.resolve(null),
    updateBook: () => Promise.resolve({}),
  },
}));

import { SoulLibrary } from "./SoulLibrary";

const book = {
  id: "b1",
  title: "Dream Journal",
  description: null,
  cover_style: "classic",
  is_archived: false,
  is_deleted: false,
  created_at: "2026-07-01T00:00:00Z",
  updated_at: "2026-07-01T00:00:00Z",
  last_opened_at: null,
  chapter_count: 2,
};

describe("SoulLibrary", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    listBooks.mockResolvedValue([book]);
    createBook.mockResolvedValue({ ...book, id: "new-book" });
    search.mockResolvedValue({ books: [], pages: [] });
  });

  it("renders the library and existing SoulBooks", async () => {
    render(<SoulLibrary />);
    expect(screen.getByText("Soul Library")).toBeInTheDocument();
    expect(await screen.findByText("Dream Journal")).toBeInTheDocument();
  });

  it("creates a SoulBook and navigates to it", async () => {
    const user = userEvent.setup();
    render(<SoulLibrary />);
    await screen.findByText("Dream Journal");
    await user.type(screen.getByLabelText("New SoulBook title"), "Song Ideas");
    await user.click(screen.getByRole("button", { name: /create soulbook/i }));
    await waitFor(() => expect(createBook).toHaveBeenCalledWith({ title: "Song Ideas" }));
    expect(push).toHaveBeenCalledWith("/soulbooks/new-book");
  });

  it("sorts SoulBooks", async () => {
    render(<SoulLibrary />);
    await screen.findByText("Dream Journal");
    fireEvent.change(screen.getByLabelText("Sort SoulBooks"), {
      target: { value: "alphabetical" },
    });
    await waitFor(() => expect(listBooks).toHaveBeenCalledWith("alphabetical", false));
  });

  it("searches SoulBooks", async () => {
    const user = userEvent.setup();
    render(<SoulLibrary />);
    await screen.findByText("Dream Journal");
    await user.type(screen.getByLabelText("Search SoulBooks"), "dream");
    await waitFor(() => expect(search).toHaveBeenCalled());
  });
});
