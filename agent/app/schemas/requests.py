"""Pydantic request models shared across the route modules."""
from typing import Optional

from pydantic import BaseModel

from app.agent.chat import ChatMessage


class PlanRequest(BaseModel):
    flags: dict[str, bool]
    memberFirstName: str
    tier: str = "free"  # client hint only; paid is verified server-side


class ChatRequest(BaseModel):
    plan: dict
    memberFirstName: str
    history: list[ChatMessage]


class AssessmentRequest(BaseModel):
    answers: dict[str, str]  # {questionId: optionValue}


class AssessmentPersonalizeRequest(BaseModel):
    answers: dict[str, str]
    memberFirstName: str


class SavePlanRequest(BaseModel):
    answers: Optional[dict] = None
    plan: Optional[dict] = None
    tracked: Optional[dict] = None
    narrative: Optional[dict] = None


class AuthStartRequest(BaseModel):
    email: str


class AuthVerifyRequest(BaseModel):
    email: str
    code: str
    # Cognito custom-auth challenge session (AUTH_BACKEND=cognito only): opaque,
    # returned by /auth/start and echoed back here. Unused for local auth.
    session: Optional[str] = None
