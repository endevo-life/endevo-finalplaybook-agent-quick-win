# Deterministic domain model (basic-enough, not 40 questions)

Each **domain** has a small set of **questions**. Each question has **tiered
answer options** (typically: fully done / partially done / not done). Each answer
maps to a specific **action item** with numbered steps. This is deterministic:
answer → action, no LLM needed for the free tier.

## Domains

| Domain | Covers |
|---|---|
| digital | accounts, devices, legacy contact, password manager, social media, docbox |
| legal | will, POA (financial + healthcare), trust, guardianship, directives |
| financial | institutions, subscriptions/autopay, housing docs, vehicle titles, life insurance, estate tax, executor duties, long-term care funding, survivor benefits |
| physical | health & caregiving: DNR/DNI, care wishes, medical contacts, long-term care |
| communication / beliefs | who-to-tell, values, funeral/memorial wishes, faith |

## Question shape (canonical)

```
QID: F1
domain: financial
question: "<the question the member is asked>"
options:
  - label: "<tier-1 answer, e.g. fully done>"
    result_type: review          # already done -> give a review checklist
    action: "<intro sentence>"
    checklist: [ "...", "...", "..." ]
  - label: "<tier-2 answer, e.g. partial>"
    result_type: steps
    action: "<intro sentence>"
    steps: [ "Step 1: ...", "Step 2: ...", "..." ]
  - label: "<tier-3 answer, e.g. not done>"
    result_type: steps
    action: "<intro sentence>"
    steps: [ "Step 1: ...", "Step 2: ...", "..." ]
```

This is a **superset** of today's `content-library.json` action-item shape (which
has `text` + optional `script`). Adopting it means the engine returns tiered,
step-by-step guidance per answer instead of one flat action item. See
`financial-domain.source.md` in this folder for a real, filled-in example (the
Financial domain, F1–F3).

## Note on richness vs. the current library

The current library is a lean scaffold (routing → a few capped action items).
The tiered question→steps model above is richer and more prescriptive. Before
migrating the whole engine to it, we should confirm with Niki/Andrea that this
tiered format is the target for all five domains — then it's a clean, mechanical
mapping.
