import { describe, it, expect } from "vitest";
import {
  actionComplete,
  domainState,
  sealedDomains,
  playbookComplete,
  overallProgress,
} from "./completion";

// A tiny Set-backed doneKeys built from ["id::0", "id::1", ...] strings.
const keys = (...ks) => new Set(ks);

const legalWill = { id: "legal_will", domain: "legal", steps: ["a", "b"] };
const legalPoa = { id: "legal_poa", domain: "legal", steps: ["a"] };
const finAcct = { id: "fin_acct", domain: "financial", steps: ["a", "b"] };

describe("actionComplete", () => {
  it("is false for an item with no steps", () => {
    expect(actionComplete({ id: "x", steps: [] }, keys())).toBe(false);
    expect(actionComplete({ id: "x" }, keys())).toBe(false);
  });

  it("is false until EVERY step is checked", () => {
    expect(actionComplete(legalWill, keys("legal_will::0"))).toBe(false);
  });

  it("is true when all steps are checked", () => {
    expect(actionComplete(legalWill, keys("legal_will::0", "legal_will::1"))).toBe(true);
  });
});

describe("domainState", () => {
  it("tallies done vs total per domain and seals only when full", () => {
    const items = [legalWill, legalPoa, finAcct];
    const s = domainState(items, keys("legal_will::0", "legal_will::1"));
    expect(s.legal).toEqual({ total: 2, done: 1, sealed: false });
    expect(s.financial.sealed).toBe(false);
  });

  it("seals a domain when all its actions complete", () => {
    const s = domainState([legalWill, legalPoa], keys(
      "legal_will::0", "legal_will::1", "legal_poa::0",
    ));
    expect(s.legal.sealed).toBe(true);
  });

  it("excludes locked items so they never block a seal", () => {
    const lockedExtra = { id: "legal_locked", domain: "legal", steps: ["a"], locked: true };
    const s = domainState([legalWill, lockedExtra], keys("legal_will::0", "legal_will::1"));
    expect(s.legal).toEqual({ total: 1, done: 1, sealed: true });
  });

  it("ignores items with no domain", () => {
    const s = domainState([{ id: "orphan", steps: ["a"] }], keys("orphan::0"));
    expect(Object.keys(s)).toHaveLength(0);
  });
});

describe("sealedDomains", () => {
  it("returns fully-sealed domains in first-appearance order", () => {
    const items = [legalWill, legalPoa, finAcct];
    const dk = keys("legal_will::0", "legal_will::1", "legal_poa::0", "fin_acct::0", "fin_acct::1");
    expect(sealedDomains(items, dk)).toEqual(["legal", "financial"]);
  });

  it("omits partially-done domains", () => {
    expect(sealedDomains([legalWill, legalPoa], keys("legal_will::0", "legal_will::1"))).toEqual([]);
  });
});

describe("playbookComplete", () => {
  it("is false when any domain is unsealed", () => {
    const items = [legalWill, finAcct];
    expect(playbookComplete(items, keys("legal_will::0", "legal_will::1"))).toBe(false);
  });

  it("is true only when every domain is sealed", () => {
    const items = [legalWill, finAcct];
    const dk = keys("legal_will::0", "legal_will::1", "fin_acct::0", "fin_acct::1");
    expect(playbookComplete(items, dk)).toBe(true);
  });

  it("is false when there are no trackable domains", () => {
    expect(playbookComplete([], keys())).toBe(false);
  });
});

describe("overallProgress", () => {
  it("is 0 when nothing trackable", () => {
    expect(overallProgress([], keys())).toBe(0);
    expect(overallProgress([{ id: "x", domain: "legal", steps: [] }], keys())).toBe(0);
  });

  it("is the fraction of completed trackable actions", () => {
    const items = [legalWill, legalPoa, finAcct]; // 3 trackable
    const dk = keys("legal_will::0", "legal_will::1"); // 1 complete
    expect(overallProgress(items, dk)).toBeCloseTo(1 / 3);
  });

  it("excludes locked items from the denominator", () => {
    const lockedExtra = { id: "l", domain: "legal", steps: ["a"], locked: true };
    const items = [legalWill, lockedExtra];
    expect(overallProgress(items, keys("legal_will::0", "legal_will::1"))).toBe(1);
  });
});
