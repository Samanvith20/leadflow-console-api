from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.auth import router as auth_router
from app.api.onboarding import router as onboarding_router
from app.api.sources import router as sources_router
from app.api.webhooks import router as webhooks_router
from app.api.workspace import router as workspace_router
from app.core.config import get_settings

# Import models during startup so Alembic and future services share one model registry.
from app.models.workspace import Workspace  # noqa: F401

settings = get_settings()

app = FastAPI(title=settings.app_name, version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "X-CSRF-Token"],
)
app.include_router(auth_router)
app.include_router(onboarding_router)
app.include_router(sources_router)
app.include_router(webhooks_router)
app.include_router(workspace_router)


@app.get("/health", tags=["system"])
def health_check() -> dict[str, str]:
    return {"status": "ok", "service": "leadflow-api", "environment": settings.environment}
