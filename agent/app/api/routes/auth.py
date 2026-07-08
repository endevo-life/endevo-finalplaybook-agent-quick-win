"""Auth routes: passwordless email login (start -> verify), session, logout."""
from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException

from app.api.deps import require_email
from app.config import AUTH_BACKEND, AUTH_RETURN_CODE
from app.schemas.requests import AuthStartRequest, AuthVerifyRequest
from app.services import analytics, auth as auth_service
from app.services.entitlements import entitlement_for

router = APIRouter(prefix="/api", tags=["auth"])


@router.post("/auth/start")
def auth_start(req: AuthStartRequest):
    # Detect a brand-new signup vs a returning user BEFORE start_login creates them.
    from app.data.store import get_store
    email_norm = (req.email or "").strip().lower()
    is_new = get_store().get_user(email_norm) is None

    if AUTH_BACKEND == "cognito":
        from app.services import auth_cognito
        try:
            session = auth_cognito.start_login(req.email)
        except ValueError as e:
            raise HTTPException(400, str(e))
        except Exception as e:
            raise HTTPException(502, f"Auth service error: {e}")
        analytics.emit(analytics.SIGNUP if is_new else analytics.LOGIN, email=email_norm)
        # Cognito emails the code; the opaque challenge session must be echoed
        # back on /auth/verify.
        return {"sent": True, "session": session}

    try:
        code = auth_service.start_login(req.email)
    except ValueError as e:
        raise HTTPException(400, str(e))
    analytics.emit(analytics.SIGNUP if is_new else analytics.LOGIN, email=email_norm)
    # In production the code is emailed as a magic link and NOT returned. In dev
    # (no email provider) we return it so you can log in. Controlled by config.
    if AUTH_RETURN_CODE:
        return {"sent": True, "devLoginCode": code}
    return {"sent": True}


@router.post("/auth/verify")
def auth_verify(req: AuthVerifyRequest):
    if AUTH_BACKEND == "cognito":
        from app.services import auth_cognito
        try:
            token = auth_cognito.verify_login(req.email, req.code, req.session or "")
        except auth_cognito.CodeRetry as e:
            # Wrong code, attempts remain: hand back the NEW single-use session
            # so the client can retry without requesting a fresh code.
            raise HTTPException(401, detail={"message": str(e), "session": e.session})
        except ValueError as e:
            raise HTTPException(401, str(e))
        except Exception as e:
            raise HTTPException(502, f"Auth service error: {e}")
        ent = entitlement_for(req.email)
        return {"token": token, "user": ent.snapshot()}

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
