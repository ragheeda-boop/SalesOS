import { company360SignalsTotal } from "../company360Signals";

describe("company360SignalsTotal", () => {
  it("returns 0 when company360/signals is missing (Vercel typecheck guard)", () => {
    expect(company360SignalsTotal(undefined)).toBe(0);
    expect(company360SignalsTotal(null)).toBe(0);
    expect(company360SignalsTotal({})).toBe(0);
  });

  it("hides badge for zero and shows count when total is positive", () => {
    expect(company360SignalsTotal({ total: 0 }) > 0).toBe(false);
    expect(company360SignalsTotal({ total: 7 })).toBe(7);
    expect(company360SignalsTotal({ total: 7 }) > 0).toBe(true);
  });
});
