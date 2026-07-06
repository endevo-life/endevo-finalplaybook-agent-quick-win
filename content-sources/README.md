# Content sources — the content engine's intake folder

**This is where you upload raw material.** Niki's session transcripts, her Excel
method sheet, Andrea's legal/digital work-item lists, and domain notes all go
here. This folder is the *input* to the content engine; the *output* is the
validated `knowledge-base/content-library.json` that the app actually runs on.

```
raw material (here)  ──mine/anonymize──▶  _processed/  ──wire──▶  knowledge-base/content-library.json  ──runs──▶  app
content-sources/                          (safe to commit)         (the deterministic rules engine reads this)
```

## ⚠️ PII — read this first

Real session transcripts and Niki's sheets contain **real people's names, health,
and financial details**. That content **must not be committed to git.**

- Everything you drop in `01-transcripts/`, `02-niki-method-excel/`,
  `03-andrea-work-items/`, and `04-domain-notes/` is **git-ignored by default** —
  it stays on your machine only.
- Only the **anonymized, structured output** you (or I) produce in `_processed/`
  gets committed, and only after names/identifiers are stripped.
- If any file must be shared, anonymize first (replace real names with `Client A`,
  `Parent`, etc.).

## Where each thing goes

| Folder | Upload here |
|---|---|
| `01-transcripts/` | Working session transcripts where Niki delivered Final Playbook (Otter exports, `.txt`/`.docx`/`.vtt`, etc.) |
| `02-niki-method-excel/` | Niki's refined method spreadsheet — the "start here → deliver Final Playbook" left-to-right sheets |
| `03-andrea-work-items/` | Andrea's deterministic **legal + digital** work-item lists |
| `04-domain-notes/` | Loose notes per domain: digital, legal, financial, physical (health/caregiving), communication/beliefs |
| `_processed/` | (Output) Anonymized, structured extracts ready to wire into the content library. **Committed.** |

## The deterministic model we're building toward

Not 40 questions — a **basic-enough, deterministic** flow across the domains
Niki actually uses:

- **Digital** · **Legal** · **Financial** · **Physical (health & caregiving)** ·
  **Communication / Beliefs**

With a fixed **"basic steps first" ordering** that's always true regardless of
situation. Per your note, the crucial always-first steps are:

1. **Doc box / "docbox"** — set up the central place for documents
2. **Legacy contact set up in phone** (first two things, every time)
3. *then* Will → POA → etc.

These "always-first, in this order" steps are captured in
[`04-domain-notes/basic-steps-first.template.md`](04-domain-notes/basic-steps-first.template.md)
so they become deterministic sequence rules in the engine, not situational
questions. See that file to fill in the canonical ordering.

## What happens after you upload

Once material is here, the extraction pass turns it into content-library shapes:
`situationProfiles`, ordered `actionItems` (with `domain` + `flag`), `scripts`,
and `definitionsGlossary` entries — each marked `validated: false` until Niki/
Andrea sign off (see `docs/guardrails.md` and the library's `_meta.status`).

**Tell me when files are in place** and I'll map Niki's Excel columns + Andrea's
work-items into the deterministic domain model and wire the "basic steps first"
sequence into `agent/rules_engine.py`.
