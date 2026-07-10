import { describe, it, expect } from "vitest";
import {
  WHY_NOW_SIGNALS,
  buildIntro,
  selectQuestions,
  reorderBySignals,
} from "./whyNowSignals";

describe("WHY_NOW_SIGNALS", () => {
  it("has 10 signals, each with a flag and label", () => {
    expect(WHY_NOW_SIGNALS).toHaveLength(10);
    for (const s of WHY_NOW_SIGNALS) {
      expect(s.flag).toBeTruthy();
      expect(s.label).toBeTruthy();
    }
  });
});

describe("buildIntro (compounding personalization)", () => {
  it("is empty with no signals", () => {
    expect(buildIntro([], "Niki")).toBe("");
  });

  it("names the person and one clause for a single signal", () => {
    const s = buildIntro(["recentNearMiss"], "Niki");
    expect(s).toContain("Niki,");
    expect(s.toLowerCase()).toContain("scare");
  });

  it("joins two signals with 'and'", () => {
    const s = buildIntro(["settledAnEstate", "worthProtecting"], "Niki");
    expect(s.toLowerCase()).toContain("estate");
    expect(s.toLowerCase()).toContain("protect");
    expect(s).toContain(", and ");
  });

  it("summarizes 3+ signals without listing them all", () => {
    const s = buildIntro(["recentLossInCircle", "becameResponsible", "digitalOutweighs"], "");
    expect(s.toLowerCase()).toContain("a few other things");
  });
});

describe("selectQuestions (gate + reorder)", () => {
  const bank = [
    { id: "FIN_contacts", domain: "financial" },
    { id: "PHYS_directive", domain: "physical" },
    { id: "DIG_pw", domain: "digital" },
    { id: "GUARD_named", domain: "legal", triggerSignals: ["becameResponsible"] },
    { id: "BIZ_succession", domain: "financial", triggerSignals: ["worthProtecting"] },
  ];

  it("hides situational questions when no signal is picked", () => {
    const ids = selectQuestions(bank, []).map((q) => q.id);
    expect(ids).not.toContain("GUARD_named");
    expect(ids).not.toContain("BIZ_succession");
    expect(ids).toContain("FIN_contacts");
  });

  it("shows and leads with the matching situational question", () => {
    const ids = selectQuestions(bank, ["becameResponsible"]).map((q) => q.id);
    expect(ids[0]).toBe("GUARD_named");
    expect(ids).not.toContain("BIZ_succession"); // other scenario stays hidden
  });

  it("is deterministic (same input → same order)", () => {
    const a = selectQuestions(bank, ["worthProtecting"]).map((q) => q.id).join(",");
    const b = selectQuestions(bank, ["worthProtecting"]).map((q) => q.id).join(",");
    expect(a).toBe(b);
  });
});

describe("reorderBySignals (plan lead)", () => {
  const items = [
    { id: "legal_will", domain: "legal", action: "Make a will" },
    { id: "digital_accounts", domain: "digital", action: "List accounts" },
    { id: "legacy_contact", domain: "digital", action: "Set a legacy contact" },
  ];

  it("keeps original order with no signals but leads doc-box/legacy-contact", () => {
    const ids = reorderBySignals(items, []).map((i) => i.id);
    // universal baseline boosts legacy contact to the front
    expect(ids[0]).toBe("legacy_contact");
  });

  it("leads with the targeted domain when a signal is picked", () => {
    const ids = reorderBySignals(items, ["digitalOutweighs"]).map((i) => i.id);
    // digital items should come before the legal one
    expect(ids.indexOf("digital_accounts")).toBeLessThan(ids.indexOf("legal_will"));
  });
});
