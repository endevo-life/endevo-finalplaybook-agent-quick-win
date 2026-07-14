# Brand & Voice Rules — My Final Playbook

Founder-locked rules from Niki + team review. These apply to **every** user-facing
surface: landing page, onboarding, questions, action steps, chat (Jesse), emails,
the PDF, and the admin console. When writing or editing any copy, follow these.

Last updated from Niki's B2C review (2026-07-12).

---

## 1. No em-dashes. Anywhere.

**Never use the `—` (em-dash) character in any user-facing text.** Not in copy,
headings, buttons, questions, steps, chat, emails, or the PDF.

- Replace with a period, comma, colon, or "and" as the sentence needs.
- This is a hard rule across all pages, from the landing page through every
  step of My Final Playbook.
- (Code comments may keep them; this is about **what users see**.)

## 2. No jargon. Plain, human language.

Banned/flagged words and their replacements:

| Don't say | Say instead |
|---|---|
| "circle" (as in "a loss in your circle") | "someone close to you", "your family", "people you love" |
| "ending" (as in "carried someone through their ending") | "final days", "passing", "when they died" |
| "intestate", "probate", "fiduciary" (unexplained) | explain in plain words, or link a glossary term |
| "the digital life you actually live" | "your accounts, photos, and passwords" |

General test: if a caring, non-lawyer friend wouldn't say it at the kitchen
table, rewrite it.

## 3. "Educate & Empower" replaces "Disclaimer"

The disclaimer strip / label is renamed to **"Educate & Empower."** Same legal
content (educational, not legal/financial/medical advice), warmer framing.

## 4. Remove the hero eyebrow line

Delete the small line above the hero headline that reads
**"MyFinalPlaybook · Digital + Legacy Planning"** (or similar). It's redundant
and clutters the top of the page.

## 5. Product name & tagline (unchanged, for reference)

- Product: **My Final Playbook** (three words, spaces).
- CTA: **Get My Final Playbook.**
- Tagline: **Live Fully ~ Die Ready.** (tilde, not comma).

## 6. Tone

- Candid about death without dread. Warm, human, plain.
- Not morbid, not clinical, not salesy/urgent.
- Educators, not legal/financial/medical advisors.

## 7. Free tier is a TASTE, not the whole thing

Keep the free experience light: about **2 steps per domain** max, not the full
40+ step plan. Free should feel achievable and invite the upgrade, not
overwhelm.

---

## How to apply

- Frontend copy lives in `frontend/src/config/branding.js` and the component
  JSX. Content (questions, steps, scripts) lives in
  `knowledge-base/content-library.json`.
- Jesse/LLM voice rules live in `agent/app/config.py` (the system prompt) and
  `agent/app/agent/signals.py` (scenario framing).
- When adding ANY new copy, re-read this file first.
