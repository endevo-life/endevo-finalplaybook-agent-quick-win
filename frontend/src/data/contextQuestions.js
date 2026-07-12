// Structured form data derived from knowledge-base/content-library.json
// contextQuestions (C1-C5). C6 ("how do you want to track this?") is
// intentionally omitted -- it has no corresponding MemberContext flag and
// would be a dead-end input in this version.
//
// Each option's `flags` object is merged into the running MemberContext
// flags as the member answers. `type` controls how QuestionStep renders it:
// "multi" = checkbox group (any number of options), "single" = pick one.

export const STEPS = [
  {
    id: "C1",
    topic: "Family composition",
    promptText: "Tell me about your family situation.",
    type: "multi",
    // purpose (per content library): determines the entire routing priority
    options: [
      { label: "I have a partner or spouse", flags: { hasPartner: true } },
      { label: "I have young children", flags: { hasYoungChildren: true } },
      { label: "I have adult children", flags: { hasAdultChildren: true } },
      { label: "I have a living parent", flags: { hasAgingParent: true } },
    ],
  },
  {
    id: "C2",
    topic: "Parent status",
    promptText: "Is your parent living independently? Do they have the three core documents, a will, power of attorney, and medical directive?",
    askIf: "hasAgingParent",
    type: "multi",
    options: [
      { label: "My parent lives alone", flags: { parentLivesAlone: true } },
      {
        label: "My parent doesn't have a will, power of attorney, or medical directive",
        flags: { parentHasNoDocs: true },
      },
    ],
  },
  {
    id: "C3",
    topic: "Document inventory",
    promptText: "What do you currently have in place? A will? Power of attorney? Medical directive? Have those been updated recently?",
    type: "multi",
    options: [
      { label: "I already have a will", flags: { hasWill: true } },
      { label: "I don't have a will yet", flags: { noWill: true } },
      { label: "I've done some planning already", flags: { hasSomeDone: true } },
      { label: "I haven't done anything yet", flags: { hasNothingDone: true } },
      { label: "I have meaningful savings, investments, or property", flags: { hasAssets: true } },
      { label: "My accounts don't have transfer-on-death set up", flags: { noTOD: true } },
    ],
  },
  {
    id: "C4",
    topic: "Life change scan",
    promptText: "Have you had any major life changes in the last 5 years?",
    type: "multi",
    options: [
      { label: "I've gone through a divorce", flags: { postDivorce: true } },
      { label: "I had a new child", flags: { newChild: true } },
      { label: "I got married recently", flags: { recentMarriage: true } },
      { label: "Someone named in my documents has passed away", flags: { deathOfNamedPerson: true } },
    ],
  },
  {
    id: "C5",
    topic: "Caregiver and business status",
    promptText: "Are you currently the primary caregiver for someone else? Do you own or co-own a business?",
    type: "multi",
    options: [
      { label: "I'm currently the primary caregiver for someone else", flags: { isCaregiver: true } },
      { label: "I own or co-own a business", flags: { isBusinessOwner: true } },
    ],
  },
  {
    id: "D1",
    topic: "Digital assessment",
    promptText: "If you died tomorrow and your phone went with you, is there a Legacy Contact set up on your account so someone could actually get in?",
    type: "single",
    options: [
      { label: "Yes, it's set up", flags: { noLegacyContact: false } },
      { label: "Maybe, not sure", flags: { noLegacyContact: true } },
      { label: "No", flags: { noLegacyContact: true } },
    ],
  },
  {
    id: "D2",
    topic: "Digital assessment",
    promptText: "Have you named someone to handle your social media if you couldn't do it yourself, and do they actually know what to do?",
    type: "single",
    options: [
      { label: "Yes, named, and they have instructions", flags: { noSocialMediaPlan: false } },
      { label: "Named, but no instructions yet", flags: { noSocialMediaPlan: true } },
      { label: "No", flags: { noSocialMediaPlan: true } },
    ],
  },
  {
    id: "D3",
    topic: "Digital assessment",
    promptText: "Are your passwords and logins somewhere a trusted person could actually find and use, a password manager, anything real?",
    type: "single",
    options: [
      { label: "Yes", flags: { noPasswordManager: false } },
      { label: "No", flags: { noPasswordManager: true } },
    ],
  },
];
