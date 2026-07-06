# Routing rules (human-readable reference)

Source of truth is `agent/rules_engine.py` + `knowledge-base/content-library.json`.
This file is a readable summary for review — if it drifts from the code, the
code wins; fix this doc to match.

**Status: DRAFT.** This logic is extracted from real client sessions
but has not yet been formally validated by the clinical author (see
`content-library.json` → `_meta.status`). Treat the priority order below
as a well-informed starting point, not a final clinical decision.

## Lead profile — first match wins

Evaluated in this exact order (`rules_engine._match_lead_profile`):

| # | Condition | Profile | Why it's ranked here |
|---|---|---|---|
| 1 | `hasAgingParent AND parentHasNoDocs` | `profile_aging_parent` | Highest urgency in the source sessions — "I just don't want you to get the call and not be able to act." |
| 2 | `postDivorce OR newChild OR recentMarriage OR deathOfNamedPerson` | `profile_post_divorce_life_change` | Beneficiary designations don't update automatically; an ex-spouse left on a 401k overrides what the will says. Must be caught before anything else. |
| 3 | `hasYoungChildren AND noWill` | `profile_young_children` | Guardian naming is the emotional unlock — without it, other decisions don't land. |
| 4 | `isSoloAger AND hasAssets` | `profile_solo_ager` | No natural heir means unset transfer-on-death designations go straight to probate. |
| 5 | `hasSomeDone OR hasWill` | `profile_pressure_test` | Existing documents ≠ a working plan — the rule is "pressure test," not "assume done." |
| 6 | `hasNothingDone` | `profile_clean_slate` | Baseline: normalize, start with one physical action, don't overwhelm. |

If none match, no lead profile is returned (the plan is empty) rather than
guessing at a default.

## Parallel profile — always additive

`profile_business_owner` fires independently of the lead profile whenever
`isBusinessOwner` is true. the clinical logic is explicit that personal and business
planning are "two separate checklists" — it never competes for the lead slot
and never gets dropped because another profile matched first.

## Action item cap

Every profile's action items are truncated to the first 5
(`MAX_ACTION_ITEMS_PER_PLAN` in `rules_engine.py`), matching the stated
rule: "I can give you a checklist and you'd be like, but we don't get it done
for multiple reasons" — more than 5 kills momentum. Business action items are
capped separately at 5 (they're a second, parallel list, not merged into the
main cap).

## What's intentionally not modeled yet

- Numeric domain scoring (legal/financial/physical/digital 0-100) — this
  needs the actual Q40 question bank with point weights, which is
  engineering/DDB territory scoped out of this content pass. This layer
  currently reasons over discrete situation profiles, not a numeric score.
- Milestone sequencing beyond one lead + one parallel profile (the original
  routing-rules document's `contextPriorityOverrides` had richer milestone
  interleaving — simplified here to what's needed for a working agent).
