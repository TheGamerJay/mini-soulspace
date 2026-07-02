import { describe, expect, it, vi } from "vitest";
import { detectTimezone, listTimezones } from "./timezone";

describe("timezone", () => {
  it("detects a timezone string", () => {
    const tz = detectTimezone();
    expect(typeof tz).toBe("string");
    expect(tz.length).toBeGreaterThan(0);
  });

  it("falls back to UTC when detection throws", () => {
    const spy = vi.spyOn(Intl, "DateTimeFormat").mockImplementation(() => {
      throw new Error("no intl");
    });
    expect(detectTimezone()).toBe("UTC");
    spy.mockRestore();
  });

  it("lists timezones for manual override", () => {
    const zones = listTimezones();
    expect(Array.isArray(zones)).toBe(true);
    expect(zones.length).toBeGreaterThan(0);
  });
});
