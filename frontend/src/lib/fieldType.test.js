import { describe, it, expect } from "vitest";
import { fieldInputType } from "./fieldType";

describe("fieldInputType", () => {
  // The bug that reached the demo: "Trusted person's name" showed a date picker
  // because the old regex matched "on" inside "pers(on)'s". Lock it forever.
  it("treats a name field as text, never a date", () => {
    expect(fieldInputType({ key: "trustedPersonName", label: "Trusted person's name" })).toBe("text");
    expect(fieldInputType({ key: "beneficiaryName", label: "Beneficiary's name" })).toBe("text");
    expect(fieldInputType({ key: "personOnFile", label: "Person on file" })).toBe("text");
  });

  it("detects real date fields", () => {
    expect(fieldInputType({ key: "legacyContactSetupDate", label: "Date set up" })).toBe("date");
    expect(fieldInputType({ key: "reviewDate", label: "Review date" })).toBe("date");
    expect(fieldInputType({ key: "x", label: "Expiry" })).toBe("date");
  });

  it("detects phone and email fields", () => {
    expect(fieldInputType({ key: "phonePlatform", label: "Phone (iPhone / Android)" })).toBe("tel");
    expect(fieldInputType({ key: "contactEmail", label: "Email address" })).toBe("email");
  });

  it("defaults to text and handles empty input", () => {
    expect(fieldInputType({ key: "relationship", label: "Relationship" })).toBe("text");
    expect(fieldInputType({})).toBe("text");
  });
});
