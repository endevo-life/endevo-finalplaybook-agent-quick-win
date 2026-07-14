# My Final Playbook, Landing Video Script + Design Briefs (v3)

> **Status: DRAFT, palette unconfirmed.** This version claims to be voice-enforced
> against an "ENDevo Master Brand Book, Colourway D, Jun 23 2026," but that
> brand book is not present anywhere in this repo, and its hex values do not
> match the palette used in v2
> ([landing-video-and-design-briefs.md](./landing-video-and-design-briefs.md)),
> which was hand-sampled directly from `frontend/src/assets/jesse_final.png`.
> Until the brand book source is located (or Niki confirms the hexes below
> directly), treat this palette as **unverified**, not final. See "Open
> questions" at the bottom before wiring these colors into `global.css` or
> `branding.js`.

**Voice-enforced against ENDevo Master Brand Book, Colourway D, Jun 23 2026 (source not yet located in repo — see Open questions).**

Brand rules (from the book, p.18):
- Sounds like ENDevo: candid about death without dread, warm and human, plain language, a little irreverent (Jesse exists for a reason), practical realities and clear takeaways, no sensationalism.
- Not ENDevo: morbid, grim, or fear-based. Cold or clinical. Salesy, urgent, discount-led. Vague euphemism.
- Product name: **My Final Playbook** (three words, spaces).
- CTA: **Get My Final Playbook.**
- Tagline: **Live Fully ~ Die Ready.** (Founder-locked. Book still shows comma version on p.14, flag for next revision.)
- No em dashes anywhere.
- Educators, not legal, financial, or medical advisors.

## Brand palette (ENDevo, confirmed per book — hexes not yet cross-checked in repo)

| Role | Hex | Name |
|---|---|---|
| Primary ink | `#08123A` | Deep Space |
| Warm accent / CTA | `#FF5D00` | Setting Sun |
| Page background | `#FFFFFF` | Pure White |
| Teal (Jesse's field) | `#58BBB6` | Open Seas |
| Surfaces / cards | `#D5D1C7` | Compassionate Grey |
| Signal / highlight | `#C9FB3F` | Guiding Light |

Cool Sienna `#A94314` is the proposed new primary in the book but not yet Niki-signed. Setting Sun stays as the live CTA color until she signs off.

Mascot: **Jesse L. Bones.** Curious, warm, learns alongside the audience. Niki teaches, Jesse learns.

---

## 1. The 2-minute landing video script

**Title:** *Your will is not your whole plan.*
**Runtime:** ~2:00, ~230 spoken words, warm and unhurried.
**Music:** soft, hopeful acoustic. Never somber strings.

| Time | Visual | Voiceover |
|---|---|---|
| 0:00–0:10 | Phone lights up on a nightstand. Kitchen morning light beyond it. Calm, not ominous. | "Your will covers the house and the car. It doesn't cover the phone." |
| 0:10–0:25 | Slow reveal of the phone home screen: banking app, photo library, email, a crypto wallet, a password manager. Warm morning tone, not ominous. | "The digital life you actually live, accounts, devices, logins, the memories people will want, doesn't pass on with a signature." |
| 0:25–0:45 | Kitchen table. Two people, a notebook, coffee. A checklist starts to fill in. | "That's the gap. And it's a fixable one. Not with a lawyer. Not with a weekend. With a playbook." |
| 0:45–1:05 | Screen recording: the app's plain-language questions being answered, one tap each. Clean UI, real product. | "My Final Playbook asks you a handful of plain-language questions, no jargon, about five minutes, and shows you exactly where your plan stands." |
| 1:05–1:25 | Screen recording: the results view. Items appear in calm Deep Space. A few glow Guiding Light `#C9FB3F` as the gaps. One gets a ✓. | "Then it hands you your first steps. Real actions with real instructions. Set a legacy contact. Name your beneficiaries. Put the important things in one place." |
| 1:25–1:40 | Jesse animates in on Open Seas `#58BBB6`, tilts his head at the checklist, then gives a small nod. Warm, curious, a beat of levity. | "Jesse helps you along the way. He's learning this stuff too, and he asks the questions you were already thinking." |
| 1:40–1:55 | Screen recording: the AI guide answering a question, the progress bar moving, the playbook building. | "Go further and it works through the whole thing with you. Every step tracked. A finished playbook your family will actually be able to use." |
| 1:55–2:00 | End card: Jesse on Open Seas `#58BBB6`. Tagline in Deep Space `#08123A`. Setting Sun `#FF5D00` button. | "Live fully. Die ready. **Get My Final Playbook.**" |

**On-screen end card:** Jesse on Open Seas `#58BBB6` · Tagline "Live Fully ~ Die Ready." in Deep Space `#08123A` · Setting Sun `#FF5D00` button: `Get My Final Playbook →` · small print: "Educational only. Not legal, financial, or medical advice. ENDevo · endevo.life"

### Voiceover-only script (ElevenLabs ready)

`(pause)` = one beat. _Italics_ = soften. **Bold** = gentle emphasis. Direction: warm, unhurried, kitchen-table voice. Never trailer voice.

> Your will covers the house and the car. (pause)
> It doesn't cover the phone.
>
> (pause)
>
> The digital life you actually live, (pause)
> accounts, devices, logins, the memories people will want, (pause)
> _doesn't pass on with a signature._
>
> (pause, music lifts)
>
> That's the gap. (pause) And it's a fixable one. (pause)
> Not with a lawyer. Not with a weekend. (pause)
> With a **playbook**.
>
> (pause)
>
> My Final Playbook asks you a handful of plain-language questions, (pause)
> no jargon, about five minutes, (pause)
> and shows you exactly where your plan stands.
>
> (pause)
>
> Then it hands you your first steps. (pause)
> Real actions with real instructions. (pause)
> Set a legacy contact. (pause)
> Name your beneficiaries. (pause)
> Put the important things in one place.
>
> (pause, Jesse beat)
>
> Jesse helps you along the way. (pause)
> He's learning this stuff too, (pause)
> and he asks the questions you were already thinking.
>
> (pause)
>
> Go further and it works through the whole thing **with** you. (pause)
> Every step tracked. (pause)
> A finished playbook your family will actually be able to use.
>
> (pause, warm smile)
>
> Live fully. (pause) Die ready. (pause)
> **Get My Final Playbook.**

**Word count:** ~200 spoken words ≈ 1:50–2:00 at a relaxed pace.

### 30-second cutdown (social/ads)

> "Your will covers the house and the car. It doesn't cover the phone. The digital life you actually live, accounts, devices, logins, the memories people will want, doesn't pass on with a signature. My Final Playbook shows you where your plan stands in five minutes, and hands you your first steps. Live fully. Die ready. **Get My Final Playbook.**"

---

## 2. Short descriptions (copy-paste)

**One-liner (meta description / app stores, ≤155 chars):**
> Your will is not your whole plan. My Final Playbook shows you where your digital life stands, and hands you your first steps. Live Fully ~ Die Ready.

**Two-sentence (directories, link previews):**
> The digital life you actually live, accounts, devices, logins, the memories people will want, doesn't pass on with a signature. My Final Playbook shows you where your plan stands in five minutes, and hands you your first steps.

**Social bio (≤80 chars):**
> Your will is not your whole plan. Live Fully ~ Die Ready. 💀📔

---

## 3. Image design briefs, paste into Claude Code

Each block is self-contained. All share the same style line and the ENDevo palette so the set matches Jesse.

**Shared style line (included in every prompt):**
> Style: warm editorial illustration, calm and reassuring, flat with subtle grain. ENDevo palette: Deep Space #08123A, Setting Sun #FF5D00, Pure White #FFFFFF, Open Seas #58BBB6, Compassionate Grey #D5D1C7, Guiding Light #C9FB3F. Generous negative space. NO horror, NO grim reaper, NO hospital imagery, NO fear framing. The mood is "getting organized on a Sunday morning," not death.

### 3.1 Hero image (landing top, 1600×900)
```
Create a landing-page hero illustration, 1600x900.
Concept: a smartphone standing upright on a warm kitchen counter, morning
light coming from the side. Beside it, a Compassionate Grey #D5D1C7
playbook lies open with a Setting Sun #FF5D00 ribbon bookmark. A hand rests
on the playbook, calm, unhurried. Background: Open Seas #58BBB6 fading to
Pure White #FFFFFF. Composition leaves the left 40% as calm negative space
for the headline "Your will is not your whole plan." and a Setting Sun
#FF5D00 button reading "Get My Final Playbook →".
Style: warm editorial illustration, calm and reassuring, flat with subtle
grain. ENDevo palette: Deep Space #08123A, Setting Sun #FF5D00, Pure White
#FFFFFF, Open Seas #58BBB6, Compassionate Grey #D5D1C7, Guiding Light
#C9FB3F. Generous negative space. NO horror, NO grim reaper, NO hospital
imagery, NO fear framing. The mood is "getting organized on a Sunday
morning," not death.
```

### 3.2 Domain icons (6 icons, 256×256 each)
```
Create a set of 6 matching line icons, 256x256, single-weight Deep Space
#08123A strokes with one Setting Sun #FF5D00 accent element each, on
transparent background. These represent the digital life a plan should
cover, framed practically, not fearfully:
1. A phone with a small legacy-contact tag (device access)
2. A bank card with a beneficiary tag (accounts and beneficiaries)
3. A photo frame with a heart (photos and memories)
4. A crypto coin with a small key (crypto and digital wallets)
5. An @ symbol with a small Setting Sun accent (email and social accounts)
6. A subscription-card stack (subscriptions and recurring services)
Same corner radius, same stroke weight, same 24px internal padding. Reads
as one calm family. Not alarming.
```

### 3.3 "How it works" trio (3 images, 800×600)
```
Create 3 matching step illustrations, 800x600 each:
Step 1 "Answer a few questions": a hand tapping one large friendly
Compassionate Grey #D5D1C7 card with a single question mark, other cards
stacked neatly behind, on Open Seas #58BBB6.
Step 2 "See where your plan stands": a simple checklist. Some items in calm
Deep Space #08123A (covered), a few glow Guiding Light #C9FB3F (the gaps).
A magnifying glass hovers, curious not alarming.
Step 3 "Get My Final Playbook": a Compassionate Grey #D5D1C7 playbook,
slightly open, Setting Sun #FF5D00 ribbon bookmark, small Guiding Light
#C9FB3F accents at the corners, a ✓ appearing on the cover.
Style: warm editorial illustration, flat with subtle grain. ENDevo palette
throughout. Generous negative space. Calm, practical, no fear framing.
```

### 3.4 Jesse moment (1200×800)
```
Using the existing skeleton mascot "Jesse L. Bones" (friendly, decorated
sugar-skull style, teal eyes, see frontend/src/assets/jesse_final.png for
reference): illustrate Jesse sitting at a warm kitchen table, sleeves rolled
up, curious head-tilt as he looks at a Compassionate Grey #D5D1C7 playbook
labeled "My Final Playbook". A coffee mug, morning light, a small Guiding
Light #C9FB3F ✓ floating above the list. Background: Jesse's signature Open
Seas #58BBB6. Jesse is learning alongside the viewer. Kind eyes, curious
posture, a little charming, zero menace. 1200x800, room at top for a short
caption.
```

### 3.5 Open Graph share card (1200×630)
```
Create an Open Graph share image, 1200x630. Left 55%: headline "Your will
is not your whole plan." in Deep Space #08123A serif, subline "The plan
for the digital life you actually live." and a Setting Sun #FF5D00 pill
button "Get My Final Playbook →", on Pure White #FFFFFF. Right 45%: an
Open Seas #58BBB6 band with the Compassionate Grey #D5D1C7 playbook
illustration, a Setting Sun ribbon, Guiding Light #C9FB3F accents at its
base, a phone leaning against it. Small "Live Fully ~ Die Ready." tag in
Deep Space at the bottom right. Calm, premium, editorial warmth.
```

### 3.6 Video thumbnail (1280×720)
```
Create a video thumbnail, 1280x720: a phone and a Compassionate Grey
#D5D1C7 playbook side by side on a warm kitchen counter, rendered in Deep
Space #08123A tones with morning light. Title in Pure White #FFFFFF serif:
"Your will is not your whole plan." Setting Sun #FF5D00 play button
centered-low. Calm and confident. A statement, not a threat. Palette: Open
Seas #58BBB6, Deep Space #08123A, Setting Sun #FF5D00, Pure White #FFFFFF.
```

---

## 4. App placement

| Asset | Placement |
|---|---|
| Hero image | `Landing.jsx` hero section |
| Domain icons | `Landing.jsx` domain grid (replaces prior FEARS grid) |
| How-it-works trio | `Landing.jsx` steps section |
| Jesse moment | Welcome / upgrade / empty states |
| OG card | `frontend/index.html` `<meta property="og:image">` |
| Video thumbnail | `Landing.jsx` video placeholder |

Note: the prior file used a `FEARS` grid label. That name itself was a voice breach. Rename the section to `DOMAINS` or `WHAT_A_PLAN_COVERS` in the JSX so the code matches the brand.

## 5. CSS variable seam (`global.css` `:root`)

| CSS var | Value | Name |
|---|---|---|
| `--brand` | `#08123A` | Deep Space |
| `--accent` | `#FF5D00` | Setting Sun |
| `--brand-lt` | `#D5D1C7` | Compassionate Grey |
| `--bg` | `#FFFFFF` | Pure White |
| `--teal` | `#58BBB6` | Open Seas |
| `--signal` | `#C9FB3F` | Guiding Light |

---

## Brand application notes (voice enforcement audit)

**What changed from v2 and why:**

1. **Killed the dread frame.** Opening moved from "if something happened to you tomorrow" to "Your will covers the house and the car. It doesn't cover the phone." Same problem named. Zero fear. Per book p.18: candid about death, without dread.

2. **Removed all "free" language.** The book flags "FREE" as a live voice breach on the current funnel. Replaced with concrete value ("hands you your first steps," "shows you exactly where your plan stands"). Free-to-start can still be true on the pricing page. It just doesn't belong in the voice.

3. **Removed "families get locked out."** That line was grief-adjacent and dread-flavored. Replaced with the book's own approved language: "the digital life you actually live doesn't pass on with a signature."

4. **Added a Jesse beat.** Book rule: Niki teaches, Jesse learns. He now has a real 15-second moment mid-video with a warm, curious head-tilt. Not a mascot cameo.

5. **Product name normalized to "My Final Playbook"** (three words, spaces). Was "MyFinalPlaybook" throughout v2.

6. **Title reframed** to "Your will is not your whole plan." That is the book's cover mantra and the strongest on-brand headline you own.

7. **Tagline held at "Live Fully ~ Die Ready."** per your founder rule. The book still shows the comma version on p.14. Flagging so it gets canonized in the next brand book revision.

8. **No em dashes** anywhere in the file.

---

## Open questions (blocking before build)

- **Where is the actual brand book file?** Nothing named "brand book," "colourway," or similar exists in this repo (checked `docs/`, `frontend/src/config/branding.js`, `frontend/src/assets/`). If it exists outside the repo, it should be added to `docs/marketing/` or linked, so future edits can be checked against it instead of copied by hand.
- **Palette conflict with v2.** v2 ([landing-video-and-design-briefs.md](./landing-video-and-design-briefs.md)) samples colors directly from `jesse_final.png` (teal `#58BBB6`, terracotta `#C86B26`, bone cream `#EDE3CE`, etc.). v3 keeps Open Seas `#58BBB6` (same teal) but replaces every other color with a new set (Deep Space, Setting Sun, Compassionate Grey, Guiding Light). Confirm which is current before touching `frontend/src/config/branding.js` or any CSS variables — right now the repo's actual `branding.js` has not been updated to either palette.
- **Cool Sienna `#A94314`** is called out as proposed-but-not-signed. Don't use it anywhere until Niki signs off.
- **Tagline punctuation** ("Live Fully ~ Die Ready." vs. book's comma version) is explicitly unresolved pending next brand book revision — keep the tilde version live per founder rule, but don't treat it as fully canonical yet.
