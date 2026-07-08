"""Chat route: grounded follow-up chat about a member's plan. Metered per tier
(free gets a small taste, paid unlimited-per-quota) and persisted per account."""
from fastapi import APIRouter, Depends, HTTPException

from app.agent.chat import chat as run_chat
from app.api.deps import require_email
from app.data.store import get_store
from app.schemas.requests import ChatRequest
from app.services import analytics
from app.services.entitlements import EntitlementError, entitlement_for

router = APIRouter(prefix="/api", tags=["chat"])


@router.post("/chat")
def create_chat_reply(req: ChatRequest, email: str = Depends(require_email)):
    if not req.history or req.history[-1].role != "user":
        raise HTTPException(400, "history must be non-empty and end with a user message")
    if len(req.history) > 40:
        raise HTTPException(400, "conversation too long -- please start a new one")

    ent = entitlement_for(email)
    try:
        ent.require_chat()
    except EntitlementError as e:
        # Free user hit the query cap (or a gate) -> a conversion signal.
        analytics.emit(analytics.CHAT_BLOCKED, email=email, code=e.code)
        raise HTTPException(e.code, str(e))

    try:
        reply = run_chat(req.plan, req.memberFirstName, req.history).model_dump()
    except Exception as e:
        raise HTTPException(502, f"Chat error: {e}")

    ent.record_chat()
    analytics.emit(analytics.CHAT, email=email, tier=ent.tier)
    # Persist the exchange so the user's AI conversation is saved per account.
    store = get_store()
    store.append_chat(email, "user", req.history[-1].content)
    store.append_chat(email, "assistant", reply["reply"])
    return reply
