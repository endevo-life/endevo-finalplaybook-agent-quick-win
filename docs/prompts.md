# Prompts

This file must always match the live prompt in `agent/personalize.py`. If you
change the code, update this doc in the same change.

## Where the LLM is used

Two call sites in the agent, both dispatching on the same `LLM_BACKEND` env
var (see `docs/guardrails.md` § 6 for why `anthropic` is default and Bedrock
is opt-in):

- `personalize()` in `agent/personalize.py`, invoked only when `tier ==
  "paid"` — the one-shot "next 30-90 days" narrative (the trial tier never calls
  an LLM at all).
- `chat()` in `agent/chat_agent.py` — grounded follow-up chat, mirrors
  `personalize.py`'s hard rules exactly (same "only use the provided plan,
  never invent advice" constraint) but multi-turn, and uses `MODEL_TRIAL`
  (cheaper/faster) instead of `MODEL_PAID` since it may be called several
  times per session. Shares `build_grounding_context()` with `personalize.py`
  so both call sites see the identical slice of the matched plan.

## Model

**`anthropic` backend (default):** `claude-sonnet-5`, no extended/adaptive
thinking configuration set (uses the model default). `claude-haiku-4-5` is
defined as `MODEL_TRIAL` for future use but is currently unused, since trial
is LLM-free by design.

**`bedrock` backend (opt-in, `LLM_BACKEND=bedrock`):** model configurable via
`BEDROCK_MODEL_ID` env var (default `meta.llama3-1-8b-instruct-v1:0`), region
via `BEDROCK_REGION` (default `us-east-1`). Auth is an AWS Bedrock API key —
set `AWS_BEARER_TOKEN_BEDROCK` in `agent/.env` (copy from `.env.example`).
Requires model access to be enabled for that model in the Bedrock console
first, in the region you're calling.

**Cost per call** (~750 cached input tokens + ~400 output tokens, per the
Anthropic pricing referenced when this was designed): roughly $0.004-0.006 on
Sonnet 5 introductory pricing. Re-check current pricing before relying on this
number for financial planning — token pricing changes.

## System prompt (verbatim, as of this writing)

```
You are helping deliver Niki Weiss's end-of-life planning guidance \
inside the Final Playbook app. We are educators and we are not legal, financial, or \
medical advisors. Niki is a digital thanatologist -- an educator, not a legal, \
financial, or medical advisor.

Hard rules:
- Only use the action items, scripts, and quotes provided in the user message below. \
Do not invent new advice, documents, laws, or numbers.
- Rephrase for warmth and clarity, but preserve the substance and Niki's direct, \
no-judgment tone (see the reference lines below).
- If the provided material doesn't cover something, say this is outside what we can \
cover here and suggest a licensed professional -- do not guess or fill the gap yourself.
- Keep the plan scoped to the next 30-90 days -- concrete and calendar-anchored where possible.
- Never present this as legal, financial, or medical advice.

Niki's reference tone lines (for calibration only -- don't insert verbatim unless it fits):
- "Live fully, die ready."
- "The worst time to plan a funeral is when someone's dead."
- "Life gets busy. It's not prioritized. That's why it takes time. There's no judgment."
```

### Why it's written this way

- **"Only use ... provided in the user message"** is the core anti-hallucination
  constraint. The user message contains only the 2-5 action items the rules
  engine already matched — never the full content library — so even if the
  model wanted to improvise, it has almost nothing ungrounded to work with.
- **"do not guess or fill the gap yourself"** exists because this is a
  sensitive-content app that must not give the impression of professional
  advice. This is a stronger instruction than typical "be helpful" framing —
  intentionally, given the domain.
- **Tone lines are for calibration, not insertion** — they're marked as
  reference material specifically so the model doesn't parrot them verbatim
  into every response, which would read as scripted rather than personalized.

## Input shape (what the model actually sees)

`personalize()` sends a JSON blob as the user message:
```json
{
  "memberFirstName": "...",
  "leadProfile": { "id": "...", "name": "...", "urgency": "..." },
  "actionItems": [ { "text": "...", "script": "..." }, ... ],
  "businessActionItems": [ ... ],
  "digitalActionItems": [ ... ],
  "supportingQuotes": [ "..." ]
}
```

## Output shape (structured, enforced via Pydantic)

```python
class PlanStep(BaseModel):
    step: str
    why_it_matters: str
    script: Optional[str] = None

class PersonalizedPlan(BaseModel):
    headline: str
    steps: list[PlanStep]
    closing_note: str
```

Enforced via `client.messages.parse(..., output_format=PersonalizedPlan)` —
the response is guaranteed to match this schema or the SDK raises, so the
frontend never has to defensively parse free-form text.

**On the `bedrock` backend**, there is no equivalent API-level enforcement.
The same schema is instead appended to the system prompt as a plain-text
instruction, the model's text response is parsed with `json.loads`, and the
result is validated against `PersonalizedPlan` after the fact. A model that
ignores the formatting instruction raises a clear `ValueError` rather than
silently passing malformed data on — but this is weaker than the Anthropic
path's guarantee. See `docs/guardrails.md` § 6.

## Prompt caching

The system prompt is marked `cache_control: {"type": "ephemeral"}` so repeat
paid-tier calls only pay full price for the system prompt once per 5-minute
cache window; subsequent calls read it at ~0.1x cost. This matters more once
volume increases — at low volume the absolute savings are small.
