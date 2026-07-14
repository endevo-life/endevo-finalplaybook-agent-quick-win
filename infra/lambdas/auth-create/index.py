"""Cognito CreateAuthChallenge trigger: generate a 6-digit sign-in code and
email it via SES as a branded HTML message (with a plain-text fallback).

On retries within one sign-in session, re-use the same code so the email the
member already received still works.

SOURCE OF TRUTH: this file. The Lambda `mfp-dev-auth-create` runs this code —
it was originally created outside the repo, so it now lives here and is
deployed with infra/lambdas/auth-create/deploy.ps1. Keep them in sync.

Env:
  FROM_EMAIL  — verified SES sender (must be hello@endevo.life or similar).
  APP_NAME    — product name shown in the email (default "My Final Playbook").
  BRAND_URL   — link shown in the footer (default endevo.life).
"""
import json
import os
import secrets

import boto3

ses = boto3.client("ses")
FROM_EMAIL = os.environ.get("FROM_EMAIL", "hello@endevo.life")
APP_NAME = os.environ.get("APP_NAME", "My Final Playbook")
BRAND_URL = os.environ.get("BRAND_URL", "endevo.life")

# ── ENDevo palette (kept inline; email clients strip <style>, so every color is
# applied as an inline attribute/style below). ────────────────────────────────
DEEP_SPACE = "#08123A"   # primary ink
SETTING_SUN = "#FF5D00"  # accent
OPEN_SEAS = "#58BBB6"    # teal band
COMP_GREY = "#D5D1C7"    # surface
BONE = "#FBFAF7"         # page bg


def _html(code: str) -> str:
    """Branded, client-safe HTML: table-based layout, inline styles, no external
    assets. Renders in Gmail/Outlook/Apple Mail. The code is big and scannable."""
    return f"""\
<!doctype html>
<html>
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head>
<body style="margin:0;padding:0;background:{BONE};font-family:-apple-system,Segoe UI,Roboto,Helvetica,Arial,sans-serif;">
  <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:{BONE};padding:32px 16px;">
    <tr><td align="center">
      <table role="presentation" width="100%" cellpadding="0" cellspacing="0"
             style="max-width:440px;background:#ffffff;border-radius:16px;overflow:hidden;
                    box-shadow:0 8px 28px -12px rgba(8,18,58,0.18);border:1px solid #ECE9E1;">
        <!-- brand band -->
        <tr><td style="background:{OPEN_SEAS};padding:22px 28px;">
          <span style="font-size:17px;font-weight:700;color:{DEEP_SPACE};letter-spacing:-0.01em;">{APP_NAME}</span>
        </td></tr>
        <!-- body -->
        <tr><td style="padding:32px 28px 8px;">
          <h1 style="margin:0 0 8px;font-size:21px;font-weight:700;color:{DEEP_SPACE};letter-spacing:-0.01em;">
            Your sign-in code
          </h1>
          <p style="margin:0 0 24px;font-size:15px;line-height:1.55;color:#45507A;">
            Enter this code in the app to finish signing in. It expires in a few minutes.
          </p>
          <!-- the code -->
          <table role="presentation" cellpadding="0" cellspacing="0" style="margin:0 auto 24px;">
            <tr><td align="center"
                    style="background:{BONE};border:1px solid {COMP_GREY};border-radius:12px;
                           padding:18px 32px;font-size:34px;font-weight:700;letter-spacing:8px;
                           color:{DEEP_SPACE};font-family:'SF Mono',Menlo,Consolas,monospace;">
              {code}
            </td></tr>
          </table>
          <p style="margin:0 0 8px;font-size:13px;line-height:1.55;color:#7C86A8;">
            Didn't request this? You can safely ignore this email — no one can sign in without the code.
          </p>
        </td></tr>
        <!-- footer -->
        <tr><td style="padding:20px 28px 26px;border-top:1px solid #F0EEE7;">
          <p style="margin:0;font-size:12px;line-height:1.5;color:#9AA1B8;">
            {APP_NAME} · <a href="https://{BRAND_URL}" style="color:{SETTING_SUN};text-decoration:none;">{BRAND_URL}</a><br>
            Educational only. Not legal, financial, or medical advice.
          </p>
        </td></tr>
      </table>
    </td></tr>
  </table>
</body>
</html>"""


def _text(code: str) -> str:
    """Plain-text fallback for clients that don't render HTML."""
    return (
        f"Your {APP_NAME} sign-in code is {code}\n\n"
        "Enter it in the app to finish signing in. It expires in a few minutes.\n\n"
        "Didn't request this? You can safely ignore this email.\n\n"
        f"{APP_NAME} · {BRAND_URL}\n"
        "Educational only. Not legal, financial, or medical advice."
    )


def handler(event, context):
    session = event["request"]["session"]
    code = None
    if session:
        try:
            code = json.loads(session[-1].get("challengeMetadata") or "{}").get("code")
        except Exception:
            code = None
    if not code:
        code = f"{secrets.randbelow(10**6):06d}"
        email = event["request"]["userAttributes"]["email"]
        try:
            ses.send_email(
                Source=FROM_EMAIL,
                Destination={"ToAddresses": [email]},
                Message={
                    "Subject": {"Data": f"Your {APP_NAME} sign-in code: {code}"},
                    "Body": {
                        "Html": {"Data": _html(code)},
                        "Text": {"Data": _text(code)},
                    },
                },
            )
        except Exception as e:
            print(f"[dev] SES send failed ({e}); check CloudWatch for the code.")
    print(f"[dev] sign-in code: {code}")  # dev convenience -- remove for prod
    event["response"]["publicChallengeParameters"] = {
        "email": event["request"]["userAttributes"].get("email", "")
    }
    event["response"]["privateChallengeParameters"] = {"code": code}
    event["response"]["challengeMetadata"] = json.dumps({"code": code})
    return event
