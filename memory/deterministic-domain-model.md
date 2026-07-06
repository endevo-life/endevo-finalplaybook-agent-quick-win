---
name: deterministic-domain-model
description: The real Final Playbook deterministic content model (tiered question -> answer -> action + steps) and the condensed consumer-app decisions
metadata:
  type: project
---

Niki/Andrea's real Final Playbook model (provided 2026-07-05) is a **tiered
deterministic** structure, NOT the lean scaffold that was in content-library.json.

**Shape:** each domain has ~9 questions. Each question has 3 tiered answer options
(roughly: fully done / partial / not done). Each answer maps to an intro action
sentence + EITHER a review checklist (when done) or numbered steps (when not).
Some digital steps carry fillable fields (trustedPersonName, dates, Face ID vs
fingerprint, where-stored). Full source captured in
`content-sources/04-domain-notes/{financial,physical,digital}-domain.source.md`.

**5 domains:** digital, legal, financial, physical (health & caregiving),
communication/beliefs.

**Basic-steps-first (always, in order, for everyone):** 1) doc box / "docbox",
2) Legacy Contact set up in phone. THEN will, POA, etc. See
`content-sources/04-domain-notes/basic-steps-first.template.md`.

**Consumer-app product decisions (user, 2026-07-05) — keep it light, NOT B2B:**
- Detail: CONDENSED. Show one clear action per answer; numbered steps go behind a
  "show me how" expander. Never a wall of tiered text.
- Flow length: BASICS-FIRST, ~1-2 highest-impact questions per domain (~8-10
  total), led by docbox + phone Legacy Contact. Not all ~45 questions.
- Wiring: financial + physical + digital wired in now (condensed); legal +
  communication/beliefs added when user provides them.

**How to apply:** content-library.json's actionItem shape needs extending to carry
tiered answers (`options: [{label, resultType: review|steps, action, checklist?,
steps?, fields?}]`). rules_engine.build_plan maps each answered question to the
matching option. Free tier still LLM-free. Raw uploads (xlsx/pdf/transcripts) are
gitignored under content-sources/; *.source.md model notes are tracked.
