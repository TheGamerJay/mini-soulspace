import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it } from "vitest";

import { ThemeSwitcher } from "./ThemeSwitcher";

describe("ThemeSwitcher", () => {
  beforeEach(() => {
    window.localStorage.clear();
    document.documentElement.dataset.theme = "";
  });

  it("applies and persists a Companion Theme (appearance only)", async () => {
    const user = userEvent.setup();
    render(<ThemeSwitcher />);
    const select = screen.getByLabelText("Companion theme");
    await user.selectOptions(select, "parchment");
    expect(document.documentElement.dataset.theme).toBe("parchment");
    expect(window.localStorage.getItem("soulspace-theme")).toBe("parchment");
  });

  it("falls back to midnight for unknown or unimplemented themes", async () => {
    window.localStorage.setItem("soulspace-theme", "rainy-day"); // architecture-ready only
    render(<ThemeSwitcher />);
    expect(document.documentElement.dataset.theme).toBe("midnight");
  });

  it("only offers implemented themes", () => {
    render(<ThemeSwitcher />);
    const options = screen.getAllByRole("option").map((o) => (o as HTMLOptionElement).value);
    expect(options).toEqual(["midnight", "parchment", "galaxy"]);
  });
});
