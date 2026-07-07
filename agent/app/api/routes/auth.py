"""Auth routes: passwordless email login (start -> verify), session, logout."""
from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException

from app.api.deps import require_email
from app.config import AUTH_RETURN_CODE
from app.schemas.requests import AuthStartRequest, AuthVerifyRequest
from app.services import auth as auth_service
from app.services.entitlements import entitlement_for

router = APIRouter(prefix="/api", tags=["auth"])


@router.post("/auth/start")
def auth_start(req: AuthStartRequest):
    try:
        code = auth_service.start_login(req.email)
    except ValueError as e:
        raise HTTPException(400, str(e))
    # In production the code is emailed as a magic link and NOT returned. In dev
    # (no email provider) we return it so you can log in. Controlled by config.
    if AUTH_RETURN_CODE:
        return {"sent": True, "devLoginCode": code}
    return {"sent": True}


@router.post("/auth/verify")
def auth_verify(req: AuthVerifyRequest):
    try:
        token = auth_service.verify_login(req.email, req.code)
    except ValueError as e:
        raise HTTPException(401, str(e))
    ent = entitlement_for(req.email)
    return {"token": token, "user": ent.snapshot()}


@router.get("/me")
def me(email: str = Depends(require_email)):
    return entitlement_for(email).snapshot()


@router.post("/auth/logout")
def auth_logout(authorization: Optional[str] = Header(None)):
    if authorization and authorization.lower().startswith("bearer "):
        auth_service.logout(authorization.split(" ", 1)[1].strip())
    return {"ok": True}
