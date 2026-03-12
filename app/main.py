from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.core.config import settings
from app.core.logging import logger
from app.api import teams_router, projects_router, prompts_router, environments_router, runs_router
from app.db.session import engine
from app.db.base import Base


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting up — DB tables verified via Alembic migrations.")
    yield
    await engine.dispose()
    logger.info("Shutdown complete.")


app = FastAPI(
    title=settings.app_name,
    description="Enterprise-grade Prompt Management & Observability API",
    version="0.1.0",
    lifespan=lifespan,
)


@app.get("/health", tags=["Health"])
async def health_check():
    logger.info("Health check called")
    return {"status": "ok"}


app.include_router(teams_router)
app.include_router(projects_router)
app.include_router(prompts_router)
app.include_router(environments_router)
app.include_router(runs_router)
