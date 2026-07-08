# MyFinalPlaybook — Landing Video Script + Design Briefs

Everything here follows the brand rules:
- The deliverable is always **"My Final Playbook"** and the CTA is always
  **"Get My Final Playbook"** — never "Get Your Final Playbook."
- Tagline: **"Live Fully, Die Ready."**
- Tone: warm, calm, plain-spoken. Fear-reduction, never fear-mongering.
  We name the fear, then immediately hand the viewer control.
- We are educators — not legal, financial, or medical advisors.

## Brand palette — derived from the Jesse mascot

The app's CSS colors are **not confirmed yet**, so all marketing assets key off
the one visual that IS confirmed: the Jesse mascot
(`frontend/src/assets/jesse_final.png`). These hexes were sampled directly
from the image:

| Role | Hex | From |
|---|---|---|
| Teal (primary / backgrounds) | `#58BBB6` | Jesse's background |
| Deep teal ink (text / dark elements) | `#103637` | Jesse's eyes |
| Terracotta (primary accent / CTA) | `#C86B26` | Jesse's hat |
| Marigold (highlight / secondary accent) | `#E68A0D` | the flowers |
| Rust brown (deep accent / borders) | `#86441B` | Jesse's suit |
| Bone cream (surfaces / cards) | `#EDE3CE` | the skull highlights |
| Warm off-white (page background) | `#FAF7F2` | neutral companion |

Mascot: "Jesse" — the Day-of-the-Dead–style skeleton mascot. Friendly, warm,
a companion — not spooky.

---

## 1. The 2-minute landing video script

**Title:** *What happens to your digital life when you die?*
**Runtime:** ~2:00 · ~280 spoken words · voice: warm, unhurried, one real person
**Music:** soft, hopeful acoustic — never somber strings

| Time | Visual | Voiceover |
|---|---|---|
| 0:00–0:08 | Black screen → a phone lights up on a nightstand with a lock screen. | "Your whole life is behind this screen. Your money. Your photos. Your passwords. So here's a hard question…" |
| 0:08–0:15 | Slow push-in on the lock screen. | "…if something happened to you tomorrow — could the people you love get in?" |
| 0:15–0:40 | Quick, gentle montage: a banking app asking for 2FA; a photo library scrolling; a crypto wallet; an email inbox. Each gets a soft padlock overlay. | "Most of us have a will for the house and the car. Almost nobody has a plan for the two-factor codes, the cloud accounts, the crypto, the subscriptions, the fifty years of photos. Families don't just grieve anymore — they get locked out." |
| 0:40–0:55 | Cut to warmth: a kitchen table, two people, a notebook, morning light. The tension releases. | "It doesn't have to be that way. And fixing it doesn't take a lawyer, or a weekend. It takes a playbook." |
| 0:55–1:15 | Screen recording: the app's quick questions being answered — one tap each. Clean UI, real product. | "MyFinalPlaybook asks you a handful of plain-language questions — no jargon, about five minutes — and finds exactly where your family would get stuck." |
| 1:15–1:35 | Screen recording: the results view. Empty checkboxes appear one by one. One gets checked ✓. | "Then it hands you your first steps, free. Real actions with real instructions — set a legacy contact, name your beneficiaries, make one place where everything important lives." |
| 1:35–1:50 | Screen recording: the AI guide answering a question; the progress bar moving; the playbook building. | "Go further and it works through the whole thing with you — every step tracked, an AI guide that knows your plan, and a finished playbook your family will actually be able to use." |
| 1:50–2:00 | Logo + Jesse mascot on his own teal `#58BBB6`. Tagline fades in, then the button. | "Live fully. Die ready. **Get My Final Playbook** — free to start." |

**On-screen end card:** Jesse on teal `#58BBB6` · "Live Fully, Die Ready." ·
button in terracotta `#C86B26`: `Get My Final Playbook →` · small print:
"Educational only — not legal, financial, or medical advice."

### Voiceover-only script (for recording / ElevenLabs voice clone)

Paste this straight into ElevenLabs (or read it aloud — ~140 wpm, relaxed).
`(pause)` = one beat of silence. _Italics_ = soften the voice; **bold** = gentle emphasis.
Voice direction: warm, unhurried, like talking to a friend at the kitchen table —
never a movie-trailer voice.

> Your whole life is behind this screen. (pause)
> Your money. Your photos. Your passwords. (pause)
> So here's a hard question. (pause)
> If something happened to you tomorrow — _could the people you love get in?_
>
> (pause)
>
> Most of us have a will for the house and the car. (pause)
> Almost nobody has a plan for the two-factor codes. The cloud accounts.
> The crypto. The subscriptions. The **fifty years of photos**. (pause)
> Families don't just grieve anymore. _They get locked out._
>
> (long pause — music lifts here)
>
> It doesn't have to be that way. (pause)
> And fixing it doesn't take a lawyer. Or a weekend. (pause)
> It takes a **playbook**.
>
> MyFinalPlaybook asks you a handful of plain-language questions —
> no jargon, about five minutes — and finds exactly where your family
> would get stuck. (pause)
> Then it hands you your first steps, **free**. (pause)
> Real actions with real instructions. Set a legacy contact.
> Name your beneficiaries. Make one place where everything important lives.
>
> (pause)
>
> Go further, and it works through the whole thing **with** you. (pause)
> Every step tracked. An AI guide that knows your plan. (pause)
> And a finished playbook your family will actually be able to use.
>
> (pause — warm smile in the voice)
>
> Live fully. (pause) Die ready. (pause)
> **Get My Final Playbook** — free to start.

**Word count:** ~200 spoken words ≈ 1:45–2:00 at a relaxed pace.

**How to produce it in Niki's voice (with her permission):**
1. Record Niki reading anything conversational for 1–2 minutes (quiet room, phone mic is fine).
2. ElevenLabs → Voices → *Instant Voice Clone* → upload the recording.
3. Paste the script above (keep the pause marks — ElevenLabs respects punctuation;
   for longer pauses use `<break time="1s" />`).
4. Generate, pick the best take, export MP3/WAV for the video edit.

### 30-second cutdown (social/ads)
> "Your money, your photos, your passwords — all behind a lock screen only you can open. If something happened to you tomorrow, your family wouldn't just grieve. They'd be locked out. MyFinalPlaybook finds the gaps in five minutes and gives you your first steps free. Live fully. Die ready. **Get My Final Playbook.**"

---

## 2. Short descriptions (copy-paste)

**One-liner (meta description / app stores, ≤155 chars):**
> The end-of-life plan nobody else covers: your digital life. Find the gaps in 5 minutes and get first steps free. Live Fully, Die Ready.

**Two-sentence (directories, link previews):**
> When you're gone, your family inherits a wall of passwords, 2FA prompts, and locked accounts. MyFinalPlaybook turns that into a clear, calm plan — answer a few plain-language questions, see exactly where you're exposed, and get first steps free.

**Social bio (≤80 chars):**
> Your digital life needs an ending plan too. Live Fully, Die Ready. 💀📔

---

## 3. Image design briefs — paste these into Claude Code

Each block below is self-contained: paste one block into Claude Code (or any
image tool) as-is. All share the same style line — sampled from the Jesse
mascot — so the whole set matches him.

**Shared style line (included in every prompt):**
> Style: warm editorial illustration in a Día-de-los-Muertos-inspired folk palette, calm and reassuring, flat with subtle grain; palette (from the Jesse mascot): teal #58BBB6, deep teal ink #103637, terracotta #C86B26, marigold #E68A0D, rust brown #86441B, bone cream #EDE3CE, warm off-white #FAF7F2; generous negative space; NO horror, NO grim reaper, NO hospital imagery; the mood is "getting organized on a Sunday morning," not death.

### 3.1 Hero image (landing top, 1600×900)
```
Create a landing-page hero illustration, 1600x900.
Concept: a smartphone standing upright like a monolith/door, slightly ajar,
warm marigold #E68A0D light spilling out of the crack; a small family
(silhouettes, deep teal #103637) stands calmly before it. The phone's lock
screen shows a padlock dissolving into a key. Background: teal #58BBB6
fading to warm off-white #FAF7F2. Composition leaves the left 40% as calm
negative space for the headline "When you're gone, will your family be
locked out of everything?" and a terracotta #C86B26 button reading
"Get My Final Playbook →".
Style: warm editorial illustration in a Día-de-los-Muertos-inspired folk
palette, calm and reassuring, flat with subtle grain; palette: teal #58BBB6,
deep teal ink #103637, terracotta #C86B26, marigold #E68A0D, rust brown
#86441B, bone cream #EDE3CE, warm off-white #FAF7F2; generous negative
space; NO horror, NO grim reaper, NO hospital imagery; the mood is
"getting organized on a Sunday morning," not death.
```

### 3.2 Fear-grid icons (6 icons, 256×256 each)
```
Create a set of 6 matching line icons, 256x256, single-weight deep teal
#103637 strokes with one marigold #E68A0D accent element each, on
transparent:
1. A phone with a small padlock (who can unlock your phone)
2. A bank card behind a shield with a "2FA" badge (online banking + 2FA)
3. A photo frame with a heart (a lifetime of photos and memories)
4. A crypto coin with a keyhole (crypto & digital wallets)
5. An @ symbol with a small marigold flower growing from it (email & social accounts)
6. A gift box with a question mark tag (do beneficiaries know what they'd inherit)
Same corner radius, same stroke weight, same 24px internal padding, so they
read as one family with the Jesse mascot's folk-art warmth. Calm and
friendly, not alarming.
```

### 3.3 "How it works" trio (3 images, 800×600)
```
Create 3 matching step illustrations, 800x600 each:
Step 1 "Answer a few questions": a hand tapping one large friendly bone-cream
#EDE3CE card with a single question mark, other cards stacked neatly behind,
on teal #58BBB6.
Step 2 "See your gaps": a simple checklist with 2 items glowing marigold
#E68A0D (exposed) and others in calm deep teal #103637 — a magnifying glass
hovers.
Step 3 "Get My Final Playbook": a bone-cream #EDE3CE playbook/binder,
slightly open, with a terracotta #C86B26 ribbon bookmark, small marigold
flowers at its corners, and a ✓ appearing on its cover.
Style: warm editorial illustration in a Día-de-los-Muertos-inspired folk
palette, calm and reassuring, flat with subtle grain; palette: teal #58BBB6,
deep teal ink #103637, terracotta #C86B26, marigold #E68A0D, rust brown
#86441B, bone cream #EDE3CE, warm off-white #FAF7F2; generous negative
space; NO horror imagery; the mood is "getting organized," not death.
```

### 3.4 Mascot moment (Jesse, 1200×800)
```
Using the existing Day-of-the-Dead skeleton mascot "Jesse" (friendly,
decorated sugar-skull style, terracotta hat with marigold flowers, rust-brown
embroidered suit, teal eyes — see frontend/src/assets/jesse_final.png for
reference): illustrate Jesse sitting at a warm kitchen table, sleeves rolled
up, cheerfully helping a person check items off a bone-cream #EDE3CE playbook
labeled "My Final Playbook". A coffee mug, morning light, a small marigold
#E68A0D ✓ floating above the list. Background: his signature teal #58BBB6.
Jesse is a companion and guide — kind eyes, relaxed posture, zero menace.
1200x800, room at top for a short caption.
```

### 3.5 Open-graph / social share card (1200×630)
```
Create an Open Graph share image, 1200x630. Left 55%: headline text
"Live Fully, Die Ready." in deep teal ink #103637 serif, subline "The plan
for your digital life — free to start" and a terracotta #C86B26 pill button
"Get My Final Playbook →", on warm off-white #FAF7F2. Right 45%: a teal
#58BBB6 band with the bone-cream #EDE3CE playbook illustration, a terracotta
ribbon, marigold #E68A0D flowers at its base, a phone leaning against it,
one marigold padlock opening. Calm, premium, folk-art warmth matching the
Jesse mascot.
```

### 3.6 Video thumbnail (1280×720)
```
Create a video thumbnail, 1280x720: a phone lock screen glowing warm in a
dim, cozy room rendered in deep teal #103637 tones, with the title in
bone-cream #EDE3CE serif: "What happens to your digital life when you die?"
and a marigold #E68A0D play button centered-low. Intriguing but gentle —
a question, not a threat. Palette: teal #58BBB6, deep teal #103637,
marigold #E68A0D, bone cream #EDE3CE.
```

---

## 4. Where these go in the app

| Asset | Placement |
|---|---|
| Hero image | `Landing.jsx` hero section background/right side |
| Fear icons | `Landing.jsx` `FEARS` grid cards |
| How-it-works trio | `Landing.jsx` steps section |
| Mascot moment | Welcome screen / upgrade moment / empty states |
| OG card | `frontend/index.html` `<meta property="og:image">` |
| Video thumbnail | `Landing.jsx` video placeholder (currently "Video coming soon") |

---

## 5. If the app adopts this palette later

When the app's colors ARE confirmed, the CSS seam is one file:
`frontend/src/styles/global.css` `:root` variables. A Jesse-matched mapping
would be roughly:

| CSS var | Today (unconfirmed) | Jesse-matched |
|---|---|---|
| `--brand` | `#1B2A4A` navy | `#103637` deep teal |
| `--accent` | `#B08D57` gold | `#C86B26` terracotta |
| `--brand-lt` | `#E9E2D2` | `#EDE3CE` bone cream |
| `--bg` | `#FAFAF9` | `#FAF7F2` warm off-white |
| highlight | — | `#E68A0D` marigold (new) |
