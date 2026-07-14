"""Cognito-backed passwordless auth (AUTH_BACKEND=cognito).

Cognito does the AUTHENTICATION (its custom-auth Lambda triggers generate,
email, and verify the 6-digit code); the app keeps its own opaque server-side
SESSION for authorization, minted on successful verification -- exactly the
same session model as the local backend (see services/auth.py for why:
instant revocation + entitlements always read fresh from the store).

Flow:
1. start_login(email) -> ensure the Cognito user exists (created silently with
   a random, never-used password so the account is CONFIRMED), kick off
   CUSTOM_AUTH. Cognito invokes the create-challenge Lambda, which emails the
   code. Returns Cognito's opaque challenge `session` string -- the client must
   echo it back on verify.
2. verify_login(email, code, session) -> answer the challenge. On success,
   mint and return our own session token (store-backed, same as local auth).

Infra this expects (created 2026-07-08, us-east-1, account 383423735462):
pool mfp-dev-users + client mfp-dev-web + Lambda triggers mfp-dev-auth-*.
NOTE: SES is in sandbox mode -- codes are only DELIVERED to verified email
addresses; for other addresses the code is visible in the create-challenge
Lambda's CloudWatch logs (dev convenience, remove before production).
"""
import secrets

from app.config import COGNITO_CLIENT_ID, COGNITO_REGION, COGNITO_USER_POOL_ID
from app.data.store import get_store
from app.services.auth import SESSION_TTL_SECONDS, _normalize_email


class CodeRetry(Exception):
    """Wrong code but attempts remain. Carries the NEW challenge session the
    client must use for its next attempt (Cognito sessions are single-use)."""
    def __init__(self, session: str):
        super().__init__("That code isn't right — try again.")
        self.session = session


def _client():
    import boto3  # lazy: only needed when AUTH_BACKEND=cognito
    return boto3.client("cognito-idp", region_name=COGNITO_REGION)


def start_login(email: str) -> str:
    """Ensure the user exists in the pool, start CUSTOM_AUTH (Cognito emails the
    code), and return the challenge session string."""
    email = _normalize_email(email)
    c = _client()

    try:
        c.admin_get_user(UserPoolId=COGNITO_USER_POOL_ID, Username=email)
    except c.exceptions.UserNotFoundException:
        c.admin_create_user(
            UserPoolId=COGNITO_USER_POOL_ID,
            Username=email,
            UserAttributes=[
                {"Name": "email", "Value": email},
                {"Name": "email_verified", "Value": "true"},
            ],
            MessageAction="SUPPRESS",  # our Lambda emails codes; no invite email
        )
        # Passwordless: the password is never used or shown -- setting a strong
        # permanent one just moves the account to CONFIRMED so CUSTOM_AUTH runs.
        c.admin_set_user_password(
            UserPoolId=COGNITO_USER_POOL_ID,
            Username=email,
            Password=secrets.token_urlsafe(40) + "Aa1!",
            Permanent=True,
        )

    resp = c.initiate_auth(
        ClientId=COGNITO_CLIENT_ID,
        AuthFlow="CUSTOM_AUTH",
        AuthParameters={"USERNAME": email},
    )

    # Mirror the user into our store so entitlements/usage exist from login #1.
    store = get_store()
    if not store.get_user(email):
        store.upsert_user(email, tier="free")

    return resp["Session"]


def verify_login(email: str, code: str, session: str) -> str:
    """Answer the emailed-code challenge. On success, mint OUR session token
    (same opaque store-backed session as local auth). Raises CodeRetry with a
    fresh challenge session on a wrong code, ValueError when out of attempts
    or the session expired."""
    email = _normalize_email(email)
    if not session:
        raise ValueError("missing auth session — request a new code")
    c = _client()
    try:
        resp = c.respond_to_auth_challenge(
            ClientId=COGNITO_CLIENT_ID,
            ChallengeName="CUSTOM_CHALLENGE",
            Session=session,
            ChallengeResponses={"USERNAME": email, "ANSWER": (code or "").strip()},
        )
    except (c.exceptions.NotAuthorizedException, c.exceptions.CodeMismatchException):
        raise ValueError("invalid or expired login code — request a new one")

    result = resp.get("AuthenticationResult")
    if not result:
        # Wrong answer, attempts remain: Cognito re-issues the challenge with a
        # NEW single-use session the client must use next time.
        raise CodeRetry(resp["Session"])

    token = secrets.token_urlsafe(32)
    get_store().create_session(token, email, SESSION_TTL_SECONDS)
    return token
