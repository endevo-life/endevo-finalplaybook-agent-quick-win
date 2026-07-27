"""AWS Lambda entrypoint. Wraps the same FastAPI `app` from app.main in Mangum so
it runs behind API Gateway with zero code changes to the routes.

In the SAM template this module's `handler` is the Lambda Handler. Locally you
run uvicorn against app.main:app -- this file is only used in the cloud.

TWO event sources reach this function:
1. API Gateway HTTP requests  -> Mangum -> FastAPI (the normal path)
2. EventBridge Scheduler      -> the weekly operator digest (Mondays 08:00 PT)

They're told apart by event shape: a scheduled invoke carries our own
{"job": "..."} payload, while an HTTP event always has requestContext. Keeping
both in one function means one deployment artifact and one set of env vars --
the digest reads the exact same store and config the API does, so its numbers
can never drift from the admin dashboard's.
"""
import logging

from mangum import Mangum

from app.main import app

log = logging.getLogger()
log.setLevel(logging.INFO)

_http = Mangum(app)


def handler(event, context):
    job = (event or {}).get("job")
    if job:
        return _run_job(job, event or {})
    return _http(event, context)


def _run_job(job: str, event: dict) -> dict:
    """Scheduled (non-HTTP) work. Always returns a dict rather than raising, so a
    failed job shows up in the logs as a result instead of a Lambda error retry
    storm -- the digest is not worth retrying automatically; it'll go out next
    week, and the admin console has a manual send button."""
    if job == "weekly_digest":
        from app.services import notifications
        result = notifications.send_weekly_digest(force=bool(event.get("force")))
        log.info("weekly_digest: %s", result)
        return result

    log.warning("unknown scheduled job: %s", job)
    return {"ok": False, "reason": f"unknown job: {job}"}
