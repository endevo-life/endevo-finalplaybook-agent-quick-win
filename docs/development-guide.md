# Development guide

## Mental model

Three layers, in order of how a request flows:

1. **`rules_engine.py`** — pure Python, no I/O, no LLM. Takes a `MemberContext`
   (booleans) and returns the matched situation profile(s) plus a capped,
   priority-ordered list of action items pulled straight from
   `content-library.json`. This is the free path — it's what the trial
   tier returns as-is.
2. **`personalize.py`** — the only place tokens are spent. Takes the output of
   step 1 and makes one Claude call to rephrase it into a personalized "next 7
   days" narrative in the product's neutral guide voice. It is never given the full content
   library, only the 2-5 already-matched items — this keeps the prompt small
   and makes ungrounded output much harder to produce.
3. **`orchestrator.py`** — glues 1 and 2 together based on `tier`.

`api.py` is a thin FastAPI wrapper around `orchestrator.run()` for local
frontend development. It is not the production transport — production moves
this into a Lambda handler (see `CLAUDE.md` → "Where this goes next").

## Adding a new situation profile

1. Add the profile to `knowledge-base/content-library.json` under
   `situationProfiles` — trigger conditions, questions, priority order, action
   items (with scripts where exact language exists), and any quotes.
   Mark it clearly if it hasn't been validated yet.
2. Add the routing rule to `_match_lead_profile()` in `rules_engine.py`. Keep
   the priority order — the function returns on the *first* match, so profile
   order in the `if` chain is itself a priority decision. Cross-check against
   `docs/rules.md` before reordering anything.
3. Add a routing test case to `agent/tests/test_rules_engine.py`.
4. No changes needed to `personalize.py` — it works generically off whatever
   `build_plan()` returns.

## Adding or changing a `MemberContext` flag

- Additive only. Existing flag names are referenced across multiple profiles
  in the content library — renaming one silently breaks routing for every
  profile that uses it, with no error (a profile just stops matching).
- After adding a flag, update `VALID_FLAGS` validation in `api.py` (it's
  derived automatically from the dataclass fields, so this is usually free)
  and add it to the relevant `FLAG_GROUPS` entry in `frontend/src/App.jsx` so
  it's actually reachable from the UI.

## Changing the personalization prompt

Edit `SYSTEM_PROMPT` in `personalize.py`, then update `docs/prompts.md` to
match — that file is meant to always reflect the live prompt, not a snapshot.
Any change that loosens the "only use what's provided" constraint should be
treated as a guardrail change, not a wording tweak — see `docs/guardrails.md`.

## Configuring credentials (`.env`)

`agent/personalize.py` loads `agent/.env` automatically via `python-dotenv` if
present. Copy `agent/.env.example` to `agent/.env` and fill in real values —
`.env` is gitignored, never commit it.

- Default backend needs only `ANTHROPIC_API_KEY`.
- To use the Bedrock backend instead, set `LLM_BACKEND=bedrock` plus
  `AWS_BEARER_TOKEN_BEDROCK`, `BEDROCK_REGION`, and `BEDROCK_MODEL_ID`. See
  `docs/prompts.md` § Model and `docs/guardrails.md` § 6 before flipping this
  switch — it trades the enforced-schema/grounding guarantees of the direct
  Anthropic path for a cheaper open-weight model.
- Restart `uvicorn` after changing `.env` — it's only read at process start.

## Local environment notes

- On Windows, prefer running `npm`/`node` commands through PowerShell rather
  than Git Bash — Git Bash's nested `cmd.exe` invocation for `npm` scripts
  failed to resolve `node` on PATH during initial setup even though `node`
  works fine directly in that same shell. PowerShell did not have this issue.
- Port 8000 was already in use by an unrelated local service when this was
  built; the backend defaults to 8001 in the run instructions for that reason,
  not for any architectural reason.
