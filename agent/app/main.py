"""FastAPI application factory. Wires the route modules and CORS. The same `app`
runs locally (uvicorn app.main:app) and in production (AWS Lambda via Mangum --
see lambda_handler.py). Transport differs; logic is identical.

Design notes:
- The free tier works with NO account (anonymous /api/plan, /api/assessment).
- Paid features (personalized plan, chat) require a logged-in user AND a live
  paid entitlement checked server-side (see app.services.entitlements).
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import DEV_CORS, PRODUCT_NAME, allowed_origins
from app.api.routes import assessment, auth, billing, chat, meta, plan


def create_app() -> FastAPI:
    app = FastAPI(title=f"{PRODUCT_NAME} API")

    # CORS: prod locks to ALLOWED_ORIGINS; dev also allows any localhost port
    # (Vite hops ports when several dev servers run).
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins(),
        allow_origin_regex=r"http://(localhost|127\.0\.0\.1):\d+" if DEV_CORS else None,
        allow_methods=["GET", "POST"],
        allow_headers=["*"],
    )

    for module in (meta, auth, assessment, plan, chat, billing):
        app.include_router(module.router)

    return app


app = create_app()
