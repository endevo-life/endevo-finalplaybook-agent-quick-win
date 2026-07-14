"""Grounded follow-up chat: lets a member ask questions about their already
-matched plan. Mirrors personalize.py's hard-rules pattern exactly, but is
multi-turn and still stateless -- the frontend resends the full message
history on every call since there is no session store (per-user persistence
is explicitly deferred, see CLAUDE.md "Where this goes next").

Grounding is the same plan slice personalize.py uses (build_grounding_context)
-- never the full content library -- and the model is never allowed to
answer outside that material. Uses MODEL_TRIAL (a smaller/cheaper model than
the one-shot personalization call) since chat may be called multiple times
per session.
"""
import json
import os
from pathlib import Path

from pydantic import BaseModel

from app.agent.personalize import MODEL_TRIAL, build_grounding_context
from app.agent.knowledge import knowledge_block

# The canonical Jesse system prompt (Niki-authored, the single source of truth).
# Edit the .txt file to change Jesse's identity/voice/guardrails; it's loaded at
# import time. The glossary knowledge block is appended so Jesse can define terms.
_PROMPT_PATH = Path(__file__).parent / "prompts" / "jesse_system.txt"
_JESSE_PROMPT = _PROMPT_PATH.read_text(encoding="utf-8")

CHAT_SYSTEM_PROMPT = f"""{_JESSE_PROMPT}

═══════════════════════════════════════════════════════════════════════
GLOSSARY AND FACTS YOU MAY DRAW ON (do not invent beyond these)
═══════════════════════════════════════════════════════════════════════
{knowledge_block()}
"""


class ChatMessage(BaseModel):
    role: str  # "user" | "assistant"
    content: str


class ChatReply(BaseModel):
    reply: str


# Chat-context directive. The canonical Jesse prompt describes the full
# engagement arc, which OPENS with a "Peace of Mind Assessment" (KICKOFF). But by
# the time a member is in chat, that assessment is ALREADY DONE -- their matched
# plan is attached below. Without this, Jesse sometimes restarts the kickoff and
# offers the assessment again, ignoring the plan (an ungrounded reply). This
# pins the chat context: the plan exists, answer from it, don't re-onboard.
# Kept here (not in jesse_system.txt) so the canonical prompt stays the shared
# source of truth across the personalize + chat call sites.
_CHAT_CONTEXT = """\
═══════════════════════════════════════════════════════════════════════
CHAT CONTEXT — READ THIS FIRST (it overrides the engagement-arc opening)
═══════════════════════════════════════════════════════════════════════
This is an ONGOING conversation about a plan the member has ALREADY built. Their
matched plan — their Readiness Actions — is provided below. Your job here is to
answer their questions using THAT plan.

- Do NOT run or offer the Peace of Mind Assessment. It is already complete.
- Do NOT greet them as if starting over or ask if they're "ready to begin."
- When they ask what to do first / next, answer from the specific actions in
  their plan below — name the actual steps, don't send them back to onboarding.
- Stay grounded in the provided plan; never invent new advice (per your hard
  rules). If something isn't covered, say so and point to a licensed professional."""


def _chat_system(signals=None) -> str:
    """CHAT_SYSTEM_PROMPT + the chat-context directive + the why-now framing.

    The chat-context directive is what keeps replies grounded in the member's
    existing plan instead of re-running the assessment kickoff (see _CHAT_CONTEXT)."""
    from app.agent.signals import framing_for
    base = f"{CHAT_SYSTEM_PROMPT}\n\n{_CHAT_CONTEXT}"
    framing = framing_for(signals)
    return base if not framing else f"{base}\n\n{framing}"


def _chat_anthropic(plan: dict, member_first_name: str, history: list[ChatMessage], signals=None) -> ChatReply:
    import anthropic  # lazy import: keeps the trial (zero-LLM) path dependency-free

    client = anthropic.Anthropic()
    response = client.messages.parse(
        model=MODEL_TRIAL,
        # 512 truncated multi-sentence answers mid-word (esp. step-by-step "how
        # do I..." replies). 1024 gives room for a complete answer while the
        # system prompt still keeps replies concise (2-5 sentences).
        max_tokens=1024,
        system=[{
            "type": "text",
            "text": _chat_system(signals),
            "cache_control": {"type": "ephemeral"},
        }, {
            "type": "text",
            "text": f"The member's matched plan (use ONLY this):\n\n{build_grounding_context(plan, member_first_name)}",
        }],
        messages=[{"role": m.role, "content": m.content} for m in history],
        output_format=ChatReply,
    )
    return response.parsed_output


def _chat_bedrock(plan: dict, member_first_name: str, history: list[ChatMessage], signals=None) -> ChatReply:
    import boto3  # lazy import: only needed when LLM_BACKEND=bedrock

    region = os.environ.get("BEDROCK_REGION", "us-east-1")
    model_id = os.environ.get("BEDROCK_MODEL_ID", "us.meta.llama3-1-8b-instruct-v1:0")
    client = boto3.client("bedrock-runtime", region_name=region)

    schema_instruction = (
        "Respond with ONLY a single valid JSON object, no markdown, no code "
        'fences, no extra commentary, matching exactly this shape: {"reply": string}'
    )
    grounding = build_grounding_context(plan, member_first_name)
    system_text = (
        f"{_chat_system(signals)}\n\nThe member's matched plan (use ONLY this):"
        f"\n\n{grounding}\n\n{schema_instruction}"
    )

    response = client.converse(
        modelId=model_id,
        system=[{"text": system_text}],
        messages=[{"role": m.role, "content": [{"text": m.content}]} for m in history],
    )
    raw_text = response["output"]["message"]["content"][0]["text"]

    try:
        data = json.loads(raw_text)
        # Only a JSON OBJECT with a string "reply" is a valid structured result.
        # Llama often returns a bare JSON string ("...answer...") or a list, which
        # json.loads() decodes fine but ChatReply(**data) can't accept -- so guard
        # the shape and otherwise fall through to the plain-text path below.
        if isinstance(data, dict) and isinstance(data.get("reply"), str):
            return ChatReply(reply=data["reply"])
        if isinstance(data, str) and data.strip():
            return ChatReply(reply=data.strip())
    except json.JSONDecodeError:
        pass  # fall through to the plain-text fallback below

    # Known reliability gap with open-weight models (see docs/guardrails.md):
    # Llama sometimes ignores the "respond with ONLY a JSON object" instruction
    # and just answers in plain text instead. The text itself is still the
    # model's grounded reply -- rather than erroring out (or spending another
    # LLM call on a retry that might fail the same way), use it directly.
    fallback_reply = raw_text.strip().strip('"').strip()
    if not fallback_reply:
        raise ValueError(
            f"Bedrock model '{model_id}' returned an empty response. Raw output: {raw_text!r}"
        )
    return ChatReply(reply=fallback_reply)


def chat(plan: dict, member_first_name: str, history: list[ChatMessage], signals=None) -> ChatReply:
    """plan is the same dict shape rules_engine.build_plan() returns. history
    must be non-empty and end with a role="user" message. `signals` are the
    member's why-now flags so Jesse leads by scenario. Backend is selected via
    LLM_BACKEND env var ("anthropic" default, or "bedrock")."""
    backend = os.environ.get("LLM_BACKEND", "anthropic")
    if backend == "bedrock":
        return _chat_bedrock(plan, member_first_name, history, signals)
    if backend == "anthropic":
        return _chat_anthropic(plan, member_first_name, history, signals)
    raise ValueError(f"Unknown LLM_BACKEND: {backend!r} (expected 'anthropic' or 'bedrock')")
