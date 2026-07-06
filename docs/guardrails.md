# Guardrails

This app is explicitly educational, not advisory ("we are not a medical,
financial, or legal advisor — we only educate"), covering a sensitive topic
(end-of-life planning). The architecture is designed so that hallucination and
scope creep are structurally hard, not just discouraged by wording.

## 1. Trial tier has no LLM in it at all

`orchestrator.run(..., tier="trial")` returns `rules_engine.build_plan()`
directly — there is no code path from trial-tier input to an LLM call. This
is the strongest guardrail available: content that never passes through a
model cannot be hallucinated by one. Verified in `tests/test_rules_engine.py`
and `tests/test_api_e2e.py` (trial-tier tests assert no `personalized` key is
ever present in the response, and require no `ANTHROPIC_API_KEY`).

## 2. The LLM only ever sees already-matched, human-authored content

`personalize()` is passed the output of `build_plan()` — 2-5 action items,
optionally a handful of quotes — never the full `content-library.json`.
The model has no ungrounded material available to draw on even if it wanted
to. This is enforced structurally (by what `personalize()`'s function
signature accepts), not just by prompt instruction.

## 3. System prompt hard rules

See `docs/prompts.md` for the full text. The load-bearing lines:
- "Only use the action items, scripts, and quotes provided in the user
  message below. Do not invent new advice, documents, laws, or numbers."
- "If the provided material doesn't cover something, say this is outside what
  we can cover here and suggest a licensed professional — do not guess."
- "Never present this as legal, financial, or medical advice."

## 4. Structured output, not free text

`output_format=PersonalizedPlan` (a Pydantic model) forces the response into
a fixed shape (`headline`, `steps[]`, `closing_note`) via the Anthropic SDK's
schema validation. This doesn't prevent hallucinated *content* inside a valid
field, but it does prevent the model from silently adding new top-level
sections, categories, or a differently-shaped response that the frontend
would render uncritically.

## 5. Content is marked as unvalidated where it is

`content-library.json`'s `_meta.status` field says this in plain text.
Anyone extending the content library should preserve that marker until the expert
and Andrea complete the validation pass described in the original routing
rules document (Section 8 of `niki_routing_rules_v1.html`), and should not
present draft content to end users as clinically final without that sign-off.

## 6. The Bedrock/open-weight backend is opt-in, not default, and weaker on guarantee #4

`personalize.py` supports a second backend (`LLM_BACKEND=bedrock`) for calling
open-weight models (Llama, Mistral, etc.) via Amazon Bedrock. This exists for
cost experimentation per earlier discussion, not as a recommended replacement
for the direct Anthropic path:
- **Default remains `anthropic`.** Switching backends requires an explicit
  env var change — it's not something that can happen by accident.
- **Guarantee #4 (structured output) is weaker here.** Bedrock's Converse API
  for open-weight models doesn't get the same API-enforced JSON schema
  validation as `client.messages.parse()`. The Bedrock path instructs the
  model to return JSON via the prompt and parses it best-effort
  (`json.loads`), raising a clear error if it fails rather than passing
  malformed data downstream — but a model that returns well-formed JSON that
  is nonetheless ungrounded would not be caught by this.
- Guarantees #1, #2, #3, and #5 above are backend-agnostic (they're
  properties of what's sent *into* the model and of the trial-tier code
  path, not of which model receives it), so they hold regardless of backend.

## What this does NOT cover yet (open risks)

- **No automated check that the model's output actually stayed grounded.**
  The system prompt instructs it to, and the input is small enough that
  drift is unlikely, but there's no post-hoc verification (e.g., checking
  that `step.text` values are substantively derived from the input
  `actionItems`). Worth adding before scaling paid-tier volume — e.g. a
  lightweight similarity/coverage check, or spot-checking transcripts.
- **No rate limiting or per-user query caps.** Explicitly deferred — this is
  agent-layer work, not SaaS-wrapper work (see `CLAUDE.md`).
- **Empty-plan edge case is guarded.** If no situation profile matches
  (`leadProfile` is `None`) and there's no parallel business checklist,
  `orchestrator.run()` returns `personalized: None` without calling the LLM
  at all — it never sends an empty plan to the model to improvise around.
  Covered by `tests/test_rules_engine.py::test_no_flags_no_llm_call`.
