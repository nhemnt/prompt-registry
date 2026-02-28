from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.core.config import settings
from app.core.logging import logger
from app.api import teams_router
from app.db.session import engine
from app.db.base import Base

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Creating database tables if they don't exist...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    await engine.dispose()

app = FastAPI(
    title=settings.app_name,
    lifespan=lifespan
)

@app.get("/health")
async def health_check():
    logger.info("Health Check Called")
    return {"status": "ok"}

app.include_router(teams_router)
