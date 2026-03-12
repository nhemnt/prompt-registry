from datetime import datetime
from fastapi import APIRouter, Depends, Query, HTTPException
from pydantic import BaseModel, ConfigDict
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.db.session import get_db
from app.models.entities import Project, Team, Prompt, PromptVersion, PromptRun
from app.core.pagination import paginate, Page, PageParams

router = APIRouter(prefix="/v1/projects", tags=["Runs"])


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

class RunCreate(BaseModel):
    version: int
    input: dict | None = None
    output: str | None = None
    latency_ms: int | None = None
    cost_usd: float | None = None
    status: str = "success"
    error: str | None = None


class RunResponse(BaseModel):
    id: int
    prompt_id: int
    version_id: int
    input: dict | None = None
    output: str | None = None
    latency_ms: int | None = None
    cost_usd: float | None = None
    status: str
    error: str | None = None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

async def get_project_or_404(team_name: str, project_name: str, db: AsyncSession) -> Project:
    query = (
        select(Project)
        .options(selectinload(Project.team))
        .join(Team, Team.id == Project.team_id)
        .where(Team.name == team_name, Project.name == project_name)
    )
    result = await db.execute(query)
    project = result.scalars().first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@router.post(
    "/{team_name}/{project_name}/{prompt_name}/runs",
    response_model=RunResponse,
    status_code=201,
)
async def log_run(
    team_name: str,
    project_name: str,
    prompt_name: str,
    payload: RunCreate,
    db: AsyncSession = Depends(get_db),
):
    """Log a prompt execution (latency, cost, input/output, status)."""
    project = await get_project_or_404(team_name, project_name, db)

    prompt_result = await db.execute(
        select(Prompt).where(Prompt.project_id == project.id, Prompt.name == prompt_name)
    )
    prompt = prompt_result.scalars().first()
    if not prompt:
        raise HTTPException(status_code=404, detail="Prompt not found")

    version_result = await db.execute(
        select(PromptVersion).where(
            PromptVersion.prompt_id == prompt.id,
            PromptVersion.version == payload.version,
        )
    )
    version = version_result.scalars().first()
    if not version:
        raise HTTPException(status_code=404, detail=f"Version {payload.version} not found")

    run = PromptRun(
        prompt_id=prompt.id,
        version_id=version.id,
        input=payload.input,
        output=payload.output,
        latency_ms=payload.latency_ms,
        cost_usd=payload.cost_usd,
        status=payload.status,
        error=payload.error,
    )
    db.add(run)
    await db.commit()
    await db.refresh(run)
    return run


@router.get(
    "/{team_name}/{project_name}/{prompt_name}/runs",
    response_model=Page[RunResponse],
)
async def get_runs(
    team_name: str,
    project_name: str,
    prompt_name: str,
    db: AsyncSession = Depends(get_db),
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=100),
    status: str | None = Query(None, description="Filter by status: success, error, timeout"),
):
    project = await get_project_or_404(team_name, project_name, db)

    prompt_result = await db.execute(
        select(Prompt).where(Prompt.project_id == project.id, Prompt.name == prompt_name)
    )
    prompt = prompt_result.scalars().first()
    if not prompt:
        raise HTTPException(status_code=404, detail="Prompt not found")

    query = (
        select(PromptRun)
        .where(PromptRun.prompt_id == prompt.id)
        .order_by(PromptRun.created_at.desc())
    )
    if status:
        query = query.where(PromptRun.status == status)

    params = PageParams(page=page, size=size)
    return await paginate(session=db, query=query, params=params)
