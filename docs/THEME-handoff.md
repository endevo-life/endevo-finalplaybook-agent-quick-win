# Theme Handoff — B2C ↔ B2B color switch

The whole app is driven by **12 CSS variables** in `frontend/src/styles/global.css`
(`:root { ... }`). 211 style rules read those variables; only ~24 stray hardcoded
hex remain (mostly the playbook-document and stat-band accents). To re-theme the
app, you change these 12 tokens. Nothing else needs to move.

This doc gives you: the token map, the current **B2C** values, a ready-to-use
**B2B (ENDevo employer)** palette, and exactly how to switch.

---

## The 12 tokens (what each controls)

| Token | Controls | B2C (current) | B2B (ENDevo) |
|---|---|---|---|
| `--bg` | Page background | `#FAFAF9` warm off-white | `#F7F9FC` cool light |
| `--surf` | Cards / surfaces | `#FFFFFF` | `#FFFFFF` |
| `--surf2` | Secondary surfaces, inputs | `#F2F0EC` warm | `#EEF2F8` cool |
| `--ink` | Headings / primary text | `#141C2E` | `#0A1B3D` ENDevo navy |
| `--body` | Body text | `#3B4557` | `#33415C` |
| `--dim` | Secondary/helper text (WCAG AA) | `#5C6577` | `#5A667E` |
| `--line` | Borders / dividers | `#E3E1D9` warm | `#DDE3ED` cool |
| `--brand` | Primary brand (buttons, headers) | `#1B2A4A` navy | `#0A1B3D` ENDevo navy |
| `--brand-lt` | Brand tint (selected, badges) | `#E9E2D2` cream | `#DCE6F5` light blue |
| `--accent` | CTA / premium / highlights | `#B08D57` gold | `#F26A21` ENDevo orange |
| `--danger` | Errors / destructive | `#A6423A` | `#D0492B` |

**Design intent of the difference:** B2C is warm (cream/gold), inviting and
personal. B2B (ENDevo employer) is cooler and more corporate (navy + the ENDevo
orange), matching endevo.life. Both keep the same structure, spacing, and
components — only the palette changes.

---

## Ready-to-use B2B `:root` (paste-replace)

Replace the `:root { ... }` block in `frontend/src/styles/global.css` with this
to switch the whole app to the B2B/ENDevo look:

```css
:root {
  --bg:       #F7F9FC;
  --surf:     #FFFFFF;
  --surf2:    #EEF2F8;
  --ink:      #0A1B3D;   /* ENDevo navy */
  --body:     #33415C;
  --dim:      #5A667E;   /* AA on white */
  --line:     #DDE3ED;
  --brand:    #0A1B3D;   /* ENDevo navy */
  --brand-lt: #DCE6F5;
  --accent:   #F26A21;   /* ENDevo orange */
  --danger:   #D0492B;
}
```

> All values meet WCAG AA contrast for their use (text tokens ≥ 4.5:1 on their
> backgrounds; `--accent` orange is used for large text / fills, not small body
> text). Verify with Kara's final brand guide before launch.

---

## How to switch (three options)

**Option A — quick swap (one theme at a time):**
Replace the `:root` block with the B2B block above, rebuild, deploy. The app is
now B2B-themed. Swap back to re-theme B2C.

**Option B — runtime toggle (both themes shippable):**
Keep B2C in `:root` and add a B2B override, then set `data-theme="b2b"` on
`<html>` to switch live:

```css
:root { /* B2C tokens (current) */ }

:root[data-theme="b2b"] {
  --bg:#F7F9FC; --surf:#FFFFFF; --surf2:#EEF2F8;
  --ink:#0A1B3D; --body:#33415C; --dim:#5A667E; --line:#DDE3ED;
  --brand:#0A1B3D; --brand-lt:#DCE6F5; --accent:#F26A21; --danger:#D0492B;
}
```
Then in JS: `document.documentElement.setAttribute("data-theme", "b2b")`.
Useful for per-tenant B2B branding (the multi-tenant B2B path).

**Option C — per-tenant (future B2B multi-tenant):**
Store each employer's palette and inject their `data-theme` (or their tokens) at
load. The 12-token system means a new tenant brand is 12 values, not a rebuild.

---

## The ~24 hardcoded hex to clean up (before heavy re-theming)

A few components use literal hex instead of tokens (they'll NOT re-theme):
- The playbook document (`.fp-pb-*`) uses paper tones (`#fffefb`, etc.) — likely
  fine to keep as "paper," but confirm.
- The stat-band and momentum gradients use `#58BBB6` teal / `#2E7F7B`.
- The Jesse chat FAB uses a teal.

If a full re-theme is needed, I can convert these to tokens (add `--teal`,
`--paper`, etc.) so 100% of the app follows the theme. Say the word.

---

## To apply a B2B theme

1. Send me the confirmed B2B palette (or use the ENDevo block above).
2. I either paste-replace `:root` (Option A) or add the override (Option B).
3. Rebuild + deploy. Done.

Because it's 12 tokens, a theme switch is minutes, not a redesign.
