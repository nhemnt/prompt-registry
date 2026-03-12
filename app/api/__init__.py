from app.api.teams import router as teams_router
from app.api.projects import router as projects_router
from app.api.prompts import router as prompts_router
from app.api.environments import router as environments_router
from app.api.runs import router as runs_router

__all__ = [
    "teams_router",
    "projects_router",
    "prompts_router",
    "environments_router",
    "runs_router",
]