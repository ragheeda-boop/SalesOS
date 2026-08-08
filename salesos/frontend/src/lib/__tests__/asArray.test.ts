import { asArray } from "../asArray";

describe("asArray", () => {
  it("returns arrays unchanged", () => {
    expect(asArray([1, 2])).toEqual([1, 2]);
  });

  it("unwraps items/data envelopes", () => {
    expect(asArray({ items: [{ id: 1 }] })).toEqual([{ id: 1 }]);
    expect(asArray({ data: ["a"] })).toEqual(["a"]);
  });

  it("returns empty for null/object without list", () => {
    expect(asArray(null)).toEqual([]);
    expect(asArray({ total: 0 })).toEqual([]);
  });
});
