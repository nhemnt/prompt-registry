from datetime import datetime
from fastapi import APIRouter, Depends, Query, HTTPException
from pydantic import BaseModel, ConfigDict
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.db.session import get_db
from app.models.entities import Project, Team, Environment, PromptEnvironment, PromptVersion, Prompt
from app.core.pagination import paginate, Page, PageParams

router = APIRouter(prefix="/v1/projects", tags=["Environments"])


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

class EnvironmentCreate(BaseModel):
    name: str
    description: str | None = None
    is_default: bool = False


class EnvironmentResponse(BaseModel):
    id: int
    name: str
    description: str | None = None
    is_default: bool
    project_id: int
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)


class DeployRequest(BaseModel):
    prompt_name: str
    version: int


class DeploymentResponse(BaseModel):
    id: int
    prompt_id: int
    environment_id: int
    version_id: int
    created_at: datetime
    updated_at: datetime
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

@router.get("/{team_name}/{project_name}/environments", response_model=Page[EnvironmentResponse])
async def get_all_environments(
    team_name: str,
    project_name: str,
    db: AsyncSession = Depends(get_db),
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=100),
):
    project = await get_project_or_404(team_name, project_name, db)
    query = select(Environment).where(Environment.project_id == project.id)
    params = PageParams(page=page, size=size)
    return await paginate(session=db, query=query, params=params)


@router.post(
    "/{team_name}/{project_name}/environments",
    response_model=EnvironmentResponse,
    status_code=201,
)
async def create_environment(
    team_name: str,
    project_name: str,
    payload: EnvironmentCreate,
    db: AsyncSession = Depends(get_db),
):
    project = await get_project_or_404(team_name, project_name, db)

    dup = await db.execute(
        select(Environment).where(
            Environment.project_id == project.id,
            Environment.name == payload.name,
        )
    )
    if dup.scalars().first():
        raise HTTPException(status_code=409, detail="Environment name already exists in this project")

    # Enforce only one default per project
    if payload.is_default:
        await db.execute(
            select(Environment).where(
                Environment.project_id == project.id,
                Environment.is_default == True,  # noqa: E712
            )
        )

    new_env = Environment(
        name=payload.name,
        description=payload.description,
        project_id=project.id,
        is_default=payload.is_default,
    )
    db.add(new_env)
    await db.commit()
    await db.refresh(new_env)
    return new_env


@router.delete("/{team_name}/{project_name}/environments/{env_name}", status_code=204)
async def delete_environment(
    team_name: str,
    project_name: str,
    env_name: str,
    db: AsyncSession = Depends(get_db),
):
    project = await get_project_or_404(team_name, project_name, db)
    result = await db.execute(
        select(Environment).where(
            Environment.project_id == project.id,
            Environment.name == env_name,
        )
    )
    env = result.scalars().first()
    if not env:
        raise HTTPException(status_code=404, detail="Environment not found")
    await db.delete(env)
    await db.commit()


@router.put(
    "/{team_name}/{project_name}/environments/{env_name}/deploy",
    response_model=DeploymentResponse,
)
async def deploy_to_environment(
    team_name: str,
    project_name: str,
    env_name: str,
    payload: DeployRequest,
    db: AsyncSession = Depends(get_db),
):
    """Pin a specific prompt version to an environment."""
    project = await get_project_or_404(team_name, project_name, db)

    env_result = await db.execute(
        select(Environment).where(
            Environment.project_id == project.id,
            Environment.name == env_name,
        )
    )
    env = env_result.scalars().first()
    if not env:
        raise HTTPException(status_code=404, detail="Environment not found")

    prompt_result = await db.execute(
        select(Prompt).where(Prompt.project_id == project.id, Prompt.name == payload.prompt_name)
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

    # Upsert — update existing deployment or create a new one
    existing_result = await db.execute(
        select(PromptEnvironment).where(
            PromptEnvironment.prompt_id == prompt.id,
            PromptEnvironment.environment_id == env.id,
        )
    )
    deployment = existing_result.scalars().first()

    if deployment:
        deployment.version_id = version.id
    else:
        deployment = PromptEnvironment(
            prompt_id=prompt.id,
            environment_id=env.id,
            version_id=version.id,
        )
        db.add(deployment)

    await db.commit()
    await db.refresh(deployment)
    return deployment
