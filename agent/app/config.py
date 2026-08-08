"""Centralized configuration -- brand/voice AND runtime settings, all read from
the environment in one discoverable place.

Brand: everything that used to hard-code a specific expert's name or personal
"clone" framing reads from here. The LLM gets a neutral, unnamed guide persona by
default; set EXPERT_NAME to surface a specific expert (guardrails are identical).

Settings: other env-driven knobs (CORS, store backend, dev flags) grouped so the
whole app's configuration surface is visible at a glance.
"""
import os

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # python-dotenv optional -- fine if env vars are set another way


# ── Brand / voice ────────────────────────────────────────────────────────────
# Matches frontend/src/config/branding.js PRODUCT_NAME. Kept identical because
# outbound mail is the same brand surface as the app -- a member or an operator
# seeing "Final Playbook" in mail and "My Final Playbook" in the UI reads as two
# different products.
PRODUCT_NAME = os.environ.get("PRODUCT_NAME", "My Final Playbook")

# Leave EXPERT_NAME empty for a neutral, unnamed guide (expert-agnostic default).
# Set it only if a specific expert is surfaced with permission.
EXPERT_NAME = os.environ.get("EXPERT_NAME", "").strip()

# Voice/attitude calibration only -- not advice, safe to ship without sign-off.
TONE_LINES = [
    "Plan while it's calm, not in a crisis.",
    "Small, concrete steps beat one overwhelming to-do list.",
    "This takes time and life gets busy -- there's no judgment here.",
]


def voice_descriptor() -> str:
    """How the LLM should describe whose guidance it's delivering."""
    if EXPERT_NAME:
        return f"{EXPERT_NAME}'s end-of-life planning guidance"
    return "professionally authored end-of-life planning guidance"


def tone_descriptor() -> str:
    """How the LLM should describe the tone to hold."""
    if EXPERT_NAME:
        return f"{EXPERT_NAME}'s direct, warm, no-judgment tone"
    return "a direct, warm, no-judgment tone"


def tone_lines_block() -> str:
    return "\n".join(f'- "{line}"' for line in TONE_LINES)


# ── Runtime settings ─────────────────────────────────────────────────────────
def allowed_origins() -> list[str]:
    raw = os.environ.get("ALLOWED_ORIGINS", "http://localhost:3200")
    return [o.strip() for o in raw.split(",") if o.strip()]


# True when ALLOWED_ORIGINS was NOT explicitly set -- dev mode, allow any
# localhost port (Vite hops ports). Production sets ALLOWED_ORIGINS to lock down.
DEV_CORS = "ALLOWED_ORIGINS" not in os.environ

# Return the login code in the response (dev, no email provider). MUST be false
# once email delivery is wired up.
AUTH_RETURN_CODE = os.environ.get("AUTH_RETURN_CODE", "true").lower() == "true"

# ── Auth backend ─────────────────────────────────────────────────────────────
# "local"   -- in-process login codes, returned in the response in dev (default;
#              zero AWS needed, what tests use).
# "cognito" -- AWS Cognito custom auth: Cognito emails the 6-digit code via the
#              pool's Lambda triggers, verifies it, and the backend then mints
#              its own session token (same opaque-session model as local).
AUTH_BACKEND = os.environ.get("AUTH_BACKEND", "local")
COGNITO_USER_POOL_ID = os.environ.get("COGNITO_USER_POOL_ID", "")
COGNITO_CLIENT_ID = os.environ.get("COGNITO_CLIENT_ID", "")
COGNITO_REGION = os.environ.get("COGNITO_REGION", os.environ.get("AWS_DEFAULT_REGION", "us-east-1"))

# Let a logged-in user unlock paid without Stripe (demos). MUST be false in prod.
ALLOW_DEV_UPGRADE = os.environ.get("ALLOW_DEV_UPGRADE", "false").lower() == "true"

# ── Email / operator notifications ───────────────────────────────────────────
# Transport for operator alerts (new signup) and the weekly digest.
# "console" -- log only, sends NOTHING (default: a dev laptop or test run can
#              never email a real person).
# "ses"     -- AWS SES v2, the same mail path Cognito uses for login codes.
# NOTE: SES has PRODUCTION access on this account, so recipients need no
# verification -- only EMAIL_FROM (the sender) must be a verified identity.
EMAIL_BACKEND = os.environ.get("EMAIL_BACKEND", "console").strip().lower()

# SES sender identity. endevo.life is a VERIFIED DOMAIN with DKIM signing on, so
# any address at that domain can send -- no per-address identity needed. A
# no-reply@ address is the right convention for automated mail: it signals
# "don't reply here" and keeps operator replies going to a monitored inbox.
# NOTE: do NOT switch to @finalplaybook.com -- that domain is registered as an
# SES identity but its DKIM was never completed (DkimStatus FAILED), so it would
# fail every send. See DEPLOY.md 3d.
EMAIL_FROM = os.environ.get("EMAIL_FROM", "no-reply@endevo.life").strip()
SES_REGION = os.environ.get(
    "SES_REGION", os.environ.get("AWS_DEFAULT_REGION", "us-east-1")
)

# Who gets signup alerts + the weekly digest. Empty = the whole notification
# feature is inert (no sends, no errors) -- the safe default.
OPERATOR_EMAILS = [
    e.strip().lower() for e in os.environ.get("OPERATOR_EMAILS", "").split(",") if e.strip()
]

# Weekly digest: kill switch + the timezone its Mon-Sun window is measured in.
DIGEST_ENABLED = os.environ.get("DIGEST_ENABLED", "true").lower() == "true"
DIGEST_TIMEZONE = os.environ.get("DIGEST_TIMEZONE", "America/Los_Angeles")


def operator_emails() -> list[str]:
    """Recipients for operator notifications. Read through a function so tests
    and a live config change see the current value, not an import-time snapshot."""
    raw = os.environ.get("OPERATOR_EMAILS")
    if raw is None:
        return list(OPERATOR_EMAILS)
    return [e.strip().lower() for e in raw.split(",") if e.strip()]


# ── Operator / admin console ─────────────────────────────────────────────────
# Shared secret that gates the admin API + dashboard. Set a strong value in prod.
# (Future: swap for the shared B2B operator Cognito pool -- lro-{env}-operator-pool.)
ADMIN_TOKEN = os.environ.get("ADMIN_TOKEN", "")

# Comma-separated allowlist of admin emails. If set, admin login requires BOTH
# the correct ADMIN_TOKEN and an email from this list. If empty, the token
# alone gates access (back-compat / early dev).
ADMIN_EMAILS = [
    e.strip().lower() for e in os.environ.get("ADMIN_EMAILS", "").split(",") if e.strip()
]

