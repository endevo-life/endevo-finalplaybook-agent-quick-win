# 04 — Domain notes

Loose notes, per domain, that don't fit a transcript or the Excel sheet — things
Niki/Andrea know that should become deterministic rules.

The five domains the model is built around:

- **digital** — accounts, devices, legacy contact, password manager, social media
- **legal** — will, POA (financial + healthcare), trust, guardianship, directives
- **financial** — accounts, beneficiaries, TOD/POD, business succession
- **physical** — health & caregiving: DNR/DNI, care wishes, medical contacts
- **communication / beliefs** — who-to-tell, values, funeral/memorial wishes, faith

Two scaffolding files live here (both committed — no PII):

- [`domain-model.template.md`](domain-model.template.md) — the deterministic
  domain + question model (basic-enough, not 40 questions).
- [`basic-steps-first.template.md`](basic-steps-first.template.md) — the
  always-first ordered steps (docbox → phone legacy contact → will/POA → …).

Fill these in (or hand me the raw material and I'll draft them), and they become
the routing/sequence rules in `agent/rules_engine.py`.
