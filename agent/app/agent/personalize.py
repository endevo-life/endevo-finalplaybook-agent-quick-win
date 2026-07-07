"""Paid-tier personalization: takes the deterministic plan from
rules_engine.build_plan() -- already matched and capped -- and turns it into a
personalized "next 7 days" narrative in the product's neutral guide voice
(see brand.py -- no single person is impersonated by default).

Only the matched profile's action items/quotes are sent, never the full content
library, to keep the prompt small and the grounding tight (the model can only
work with what's in front of it).

Two backends are supported, selected via the LLM_BACKEND env var:
- "anthropic" (default) -- direct Claude API call with enforced structured
  output (client.messages.parse). This is the recommended path for the
  sensitive-content grounded-advice generation this app does.
- "bedrock" -- an explicit opt-in to call an open-weight model (Llama,
  Mistral, etc.) via Amazon Bedrock instead. See docs/guardrails.md before
  using this for anything beyond experimentation -- open-weight models are
  weaker at staying grounded and don't get the same enforced-schema guarantee
  (their JSON output is parsed best-effort, not schema-validated by the API).
"""
import json
import os
from typing import Optional

from pydantic import BaseModel

from app.config import (
    PRODUCT_NAME,
    tone_descriptor,
    tone_lines_block,
    voice_descriptor,
)

MODEL_TRIAL = "claude-haiku-4-5"  # not currently called -- trial tier is LLM-free by design
MODEL_PAID = "claude-sonnet-5"

SYSTEM_PROMPT = f"""You are the guide inside the {PRODUCT_NAME} app, helping deliver \
{voice_descriptor()}. We are educators and we are not legal, financial, or medical \
advisors.

Hard rules:
- Only use the action items, scripts, and quotes provided in the user message below. \
Do not invent new advice, documents, laws, or numbers.
- Rephrase for warmth and clarity, but preserve the substance and hold {tone_descriptor()} \
(see the reference lines below).
- If the provided material doesn't cover something, say this is outside what we can \
cover here and suggest a licensed professional -- do not guess or fill the gap yourself.
- Keep the plan scoped to the next 7 days -- concrete and calendar-anchored where possible.
- Never present this as legal, financial, or medical advice.

Reference tone lines (for calibration only -- don't insert verbatim unless it fits):
{tone_lines_block()}
"""


class PlanStep(BaseModel):
    step: str
    why_it_matters: str
    script: Optional[str] = None


class PersonalizedPlan(BaseModel):
    headline: str
    steps: list[PlanStep]
    closing_note: str


def build_grounding_context(plan: dict, member_first_name: str) -> str:
    """Serializes the matched plan into the JSON blob sent to the model as
    grounding data. Shared with chat_agent.py -- both call sites must see
    exactly the same slice of the plan, never the full content library."""
    return json.dumps({
        "memberFirstName": member_first_name,
        "leadProfile": plan.get("leadProfile"),
        "actionItems": plan.get("actionItems"),
        "businessActionItems": plan.get("businessActionItems"),
        "digitalActionItems": plan.get("digitalActionItems"),
        "supportingQuotes": plan.get("quotes"),
    }, indent=2)


def _personalize_anthropic(plan: dict, member_first_name: str) -> PersonalizedPlan:
    import anthropic  # lazy import: keeps the trial (zero-LLM) path dependency-free

    client = anthropic.Anthropic()
    user_content = build_grounding_context(plan, member_first_name)

    response = client.messages.parse(
        model=MODEL_PAID,
        # A full personalized plan (headline + up to 5 steps, each with a script,
        # + closing note) can run past 1024 tokens; too low a cap truncates the
        # JSON mid-string and the structured parse fails. 3072 gives the whole
        # plan room to close cleanly while staying cheap.
        max_tokens=3072,
        system=[{
            "type": "text",
            "text": SYSTEM_PROMPT,
            "cache_control": {"type": "ephemeral"},
        }],
        messages=[{
            "role": "user",
            "content": f"Build this member's next-7-days plan from ONLY this data:\n\n{user_content}",
        }],
        output_format=PersonalizedPlan,
    )
    return response.parsed_output


def _personalize_bedrock(plan: dict, member_first_name: str) -> PersonalizedPlan:
    import boto3  # lazy import: only needed when LLM_BACKEND=bedrock

    region = os.environ.get("BEDROCK_REGION", "us-east-1")
    model_id = os.environ.get("BEDROCK_MODEL_ID", "meta.llama3-1-8b-instruct-v1:0")
    client = boto3.client("bedrock-runtime", region_name=region)
    user_content = build_grounding_context(plan, member_first_name)

    schema_instruction = (
        "Respond with ONLY a single valid JSON object, no markdown, no code "
        "fences, no extra commentary, matching exactly this shape: "
        '{"headline": string, "steps": [{"step": string, '
        '"why_it_matters": string, "script": string or null}], '
        '"closing_note": string}'
    )

    response = client.converse(
        modelId=model_id,
        system=[{"text": SYSTEM_PROMPT + "\n\n" + schema_instruction}],
        messages=[{
            "role": "user",
            "content": [{"text": f"Build this member's next-7-days plan from ONLY this data:\n\n{user_content}"}],
        }],
    )
    raw_text = response["output"]["message"]["content"][0]["text"]

    try:
        data = json.loads(raw_text)
    except json.JSONDecodeError as e:
        raise ValueError(
            f"Bedrock model '{model_id}' did not return valid JSON (this is a "
            f"known reliability gap with open-weight models -- see "
            f"docs/guardrails.md). Raw output: {raw_text!r}"
        ) from e

    return PersonalizedPlan(**data)


def personalize(plan: dict, member_first_name: str) -> PersonalizedPlan:
    """plan is the dict returned by rules_engine.build_plan(). Backend is
    selected via LLM_BACKEND env var ("anthropic" default, or "bedrock")."""
    backend = os.environ.get("LLM_BACKEND", "anthropic")
    if backend == "bedrock":
        return _personalize_bedrock(plan, member_first_name)
    if backend == "anthropic":
        return _personalize_anthropic(plan, member_first_name)
    raise ValueError(f"Unknown LLM_BACKEND: {backend!r} (expected 'anthropic' or 'bedrock')")
