import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";
import { PasswordInput } from "./PasswordInput";

describe("PasswordInput", () => {
  it("starts hidden with the 🙈 toggle and masks input", () => {
    render(<PasswordInput aria-label="pw" defaultValue="secret" />);
    const input = screen.getByLabelText("pw") as HTMLInputElement;
    const toggle = screen.getByRole("button", { name: /show password/i });
    expect(input.type).toBe("password");
    expect(toggle).toHaveTextContent("🙈");
  });

  it("reveals with 👁️ when toggled, and hides again", async () => {
    const user = userEvent.setup();
    render(<PasswordInput aria-label="pw" defaultValue="secret" />);
    const input = screen.getByLabelText("pw") as HTMLInputElement;
    const toggle = screen.getByRole("button", { name: /show password/i });

    await user.click(toggle);
    expect(input.type).toBe("text");
    expect(screen.getByRole("button", { name: /hide password/i })).toHaveTextContent("👁️");

    await user.click(screen.getByRole("button", { name: /hide password/i }));
    expect(input.type).toBe("password");
  });
});
