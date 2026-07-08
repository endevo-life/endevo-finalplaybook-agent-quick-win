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

from pydantic import BaseModel

from app.config import PRODUCT_NAME, tone_descriptor, tone_lines_block
from app.agent.personalize import MODEL_TRIAL, build_grounding_context

CHAT_SYSTEM_PROMPT = f"""You are the guide answering a member's follow-up questions \
inside the {PRODUCT_NAME} app. We are educators and we are not legal, financial, or \
medical advisors.

Hard rules:
- Only use the action items, scripts, and quotes in the member's matched plan below. \
Do not invent new advice, documents, laws, or numbers.
- If the member asks something the plan below doesn't cover, say plainly that it's \
outside what's covered here and suggest a licensed professional -- do not guess.
- Keep replies short (2-5 sentences unless listing plan items requires more) and hold \
{tone_descriptor()}.
- Never present this as legal, financial, or medical advice.
- If asked something unrelated to end-of-life planning or this member's plan, politely \
redirect back to the plan.

Reference tone lines (for calibration only -- don't insert verbatim unless it fits):
{tone_lines_block()}
"""


class ChatMessage(BaseModel):
    role: str  # "user" | "assistant"
    content: str


class ChatReply(BaseModel):
    reply: str


def _system_with_grounding(plan: dict, member_first_name: str) -> str:
    grounding = build_grounding_context(plan, member_first_name)
    return f"{CHAT_SYSTEM_PROMPT}\n\nThe member's matched plan (use ONLY this):\n\n{grounding}"


def _chat_anthropic(plan: dict, member_first_name: str, history: list[ChatMessage]) -> ChatReply:
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
            "text": CHAT_SYSTEM_PROMPT,
            "cache_control": {"type": "ephemeral"},
        }, {
            "type": "text",
            "text": f"The member's matched plan (use ONLY this):\n\n{build_grounding_context(plan, member_first_name)}",
        }],
        messages=[{"role": m.role, "content": m.content} for m in history],
        output_format=ChatReply,
    )
    return response.parsed_output


def _chat_bedrock(plan: dict, member_first_name: str, history: list[ChatMessage]) -> ChatReply:
    import boto3  # lazy import: only needed when LLM_BACKEND=bedrock

    region = os.environ.get("BEDROCK_REGION", "us-east-1")
    model_id = os.environ.get("BEDROCK_MODEL_ID", "us.meta.llama3-1-8b-instruct-v1:0")
    client = boto3.client("bedrock-runtime", region_name=region)

    schema_instruction = (
        "Respond with ONLY a single valid JSON object, no markdown, no code "
        'fences, no extra commentary, matching exactly this shape: {"reply": string}'
    )

    response = client.converse(
        modelId=model_id,
        system=[{"text": _system_with_grounding(plan, member_first_name) + "\n\n" + schema_instruction}],
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


def chat(plan: dict, member_first_name: str, history: list[ChatMessage]) -> ChatReply:
    """plan is the same dict shape rules_engine.build_plan() returns. history
    must be non-empty and end with a role="user" message. Backend is
    selected via LLM_BACKEND env var ("anthropic" default, or "bedrock")."""
    backend = os.environ.get("LLM_BACKEND", "anthropic")
    if backend == "bedrock":
        return _chat_bedrock(plan, member_first_name, history)
    if backend == "anthropic":
        return _chat_anthropic(plan, member_first_name, history)
    raise ValueError(f"Unknown LLM_BACKEND: {backend!r} (expected 'anthropic' or 'bedrock')")
