// Maps the 6 real scenario cards (+ business-owner add-on) to the exact
// MemberContext flags defined in agent/rules_engine.py. Kept 1:1 with the
// backend's 19 valid flags -- do not invent new flag names here.
import {
  faHouse,
  faBaby,
  faCompass,
  faArrowsRotate,
  faClipboardCheck,
  faSeedling,
} from "@fortawesome/free-solid-svg-icons";

export const SCENARIOS = [
  {
    id: "parent",
    icon: faHouse,
    title: "My aging parent needs a plan",
    sub: "Worried about a parent who may not have documents in order",
    baseFlags: { hasAgingParent: true },
  },
  {
    id: "kids",
    icon: faBaby,
    title: "I have young children",
    sub: "No guardian named, or nothing in writing yet",
    baseFlags: { hasYoungChildren: true },
  },
  {
    id: "solo",
    icon: faCompass,
    title: "It's just me",
    sub: "No partner or children, I need my own plan",
    baseFlags: { isSoloAger: true },
  },
  {
    id: "change",
    icon: faArrowsRotate,
    title: "Something changed recently",
    sub: "Divorce, marriage, a new child, or a loss in the last 5 years",
    baseFlags: {},
    // This scenario doesn't map to one flag -- it needs a follow-up choice.
    needsSubchoice: true,
    subchoiceQuestion: "Which of these applies?",
    subchoiceOptions: [
      { label: "Divorce", flag: "postDivorce" },
      { label: "New child", flag: "newChild" },
      { label: "Recent marriage", flag: "recentMarriage" },
      { label: "Death of someone named in my documents", flag: "deathOfNamedPerson" },
    ],
  },
  {
    id: "some_done",
    icon: faClipboardCheck,
    title: "I've done some of this",
    sub: "I have documents already but want to check they still hold up",
    baseFlags: { hasSomeDone: true },
  },
  {
    id: "fresh",
    icon: faSeedling,
    title: "I'm starting from scratch",
    sub: "I haven't done anything and don't know where to begin",
    baseFlags: { hasNothingDone: true },
  },
];

// isBusinessOwner is always additive/parallel in rules_engine.py -- it never
// competes for the lead profile slot, so it's a standalone toggle rather
// than a 7th scenario card.
export const BUSINESS_OWNER_FLAG = "isBusinessOwner";
