import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { InkText } from "./InkText";

describe("InkText", () => {
  it("renders the full reflection text as accessible journal writing", () => {
    const text = "Ink appears like a quiet fountain pen.";
    render(<InkText text={text} />);
    const paragraph = screen.getByLabelText(text);
    expect(paragraph).toBeInTheDocument();
    expect(paragraph.textContent).toBe(text); // every word present immediately
  });

  it("staggers word animation delays like handwriting", () => {
    render(<InkText text="one two three" />);
    const words = document.querySelectorAll(".ink-word");
    expect(words.length).toBe(3);
    const delays = Array.from(words).map((w) => (w as HTMLElement).style.animationDelay);
    expect(new Set(delays).size).toBe(3); // each word begins after the last
  });
});
