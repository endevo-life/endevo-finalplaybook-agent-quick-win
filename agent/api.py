"""Thin local dev API exposing the agent to the React UI. In production this
logic moves into a Lambda handler behind API Gateway -- same orchestrator.run()
call, different transport.
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from chat_agent import ChatMessage, chat as run_chat
from orchestrator import run
from rules_engine import CONTENT_LIBRARY, MemberContext

app = FastAPI(title="Final Playbook Agent (dev)")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Vite dev server
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# Run with: python -m uvicorn api:app --port 8001
# (port 8000 was occupied by an unrelated service on this machine)

VALID_FLAGS = set(MemberContext.__dataclass_fields__.keys())


class PlanRequest(BaseModel):
    flags: dict[str, bool]
    memberFirstName: str
    tier: str = "trial"


class ChatRequest(BaseModel):
    plan: dict
    memberFirstName: str
    history: list[ChatMessage]


@app.get("/api/glossary")
def get_glossary():
    """Grounded term definitions for UI tooltips -- sourced from the content
    library's definitionsGlossary, not invented in the frontend. See
    niki-content-library.json _meta.status: draft, not yet reviewed by Niki."""
    return CONTENT_LIBRARY.get("definitionsGlossary", [])


@app.post("/api/plan")
def create_plan(req: PlanRequest):
    unknown = set(req.flags) - VALID_FLAGS
    if unknown:
        raise HTTPException(400, f"Unknown flags: {sorted(unknown)}")
    if req.tier not in ("trial", "paid"):
        raise HTTPException(400, "tier must be 'trial' or 'paid'")

    try:
        return run(req.flags, req.memberFirstName, tier=req.tier)
    except Exception as e:
        # Paid tier needs ANTHROPIC_API_KEY configured -- surface that clearly
        # rather than a raw stack trace.
        raise HTTPException(502, f"Agent error: {e}")


@app.post("/api/chat")
def create_chat_reply(req: ChatRequest):
    if not req.history or req.history[-1].role != "user":
        raise HTTPException(400, "history must be non-empty and end with a user message")
    if len(req.history) > 40:
        raise HTTPException(400, "conversation too long -- please start a new one")

    try:
        return run_chat(req.plan, req.memberFirstName, req.history).model_dump()
    except Exception as e:
        raise HTTPException(502, f"Chat error: {e}")
