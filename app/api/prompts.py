from datetime import datetime
from fastapi import APIRouter, Depends, Query, HTTPException
from pydantic import BaseModel, ConfigDict
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
import re

from app.db.session import get_db
from app.models.entities import Project, Team, Prompt, PromptVersion
from app.core.pagination import paginate, Page, PageParams

router = APIRouter(prefix="/v1/prompts", tags=["Prompts"])


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

class ProjectNested(BaseModel):
    id: int
    name: str
    model_config = ConfigDict(from_attributes=True)


class PromptCreate(BaseModel):
    name: str
    description: str | None = None


class PromptUpdate(BaseModel):
    description: str | None = None
    is_active: bool | None = None


class VersionCreate(BaseModel):
    content: str
    commit_message: str
    model_hint: str | None = None
    temperature: float | None = None
    max_tokens: int | None = None


class VersionResponse(BaseModel):
    id: int
    version: int
    content: str
    variables: list[str]
    model_hint: str | None = None
    temperature: float | None = None
    max_tokens: int | None = None
    commit_message: str | None = None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class HeadVersionSummary(BaseModel):
    id: int
    version: int
    model_config = ConfigDict(from_attributes=True)


class PromptResponse(BaseModel):
    id: int
    name: str
    description: str | None = None
    is_active: bool
    head_version_id: int | None = None
    head_version: HeadVersionSummary | None = None
    project: ProjectNested
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)


class PromptDetailResponse(PromptResponse):
    versions: list[VersionResponse] = []


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def extract_variables(content: str) -> list[str]:
    """Extract {{variable}} placeholders from prompt content."""
    return sorted(set(re.findall(r"\{\{(\w+)\}\}", content)))


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


async def get_prompt_or_404(project: Project, prompt_name: str, db: AsyncSession) -> Prompt:
    query = (
        select(Prompt)
        .options(selectinload(Prompt.head_version))
        .where(Prompt.project_id == project.id, Prompt.name == prompt_name)
    )
    result = await db.execute(query)
    prompt = result.scalars().first()
    if not prompt:
        raise HTTPException(status_code=404, detail="Prompt not found")
    prompt.project = project
    return prompt


# ---------------------------------------------------------------------------
# Prompt routes
# ---------------------------------------------------------------------------

@router.get("/{team_name}/{project_name}", response_model=Page[PromptResponse])
async def get_all_prompts(
    team_name: str,
    project_name: str,
    db: AsyncSession = Depends(get_db),
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=100),
    active_only: bool = Query(True, description="Filter to active prompts only"),
):
    project = await get_project_or_404(team_name, project_name, db)

    query = (
        select(Prompt)
        .options(selectinload(Prompt.head_version))
        .where(Prompt.project_id == project.id)
    )
    if active_only:
        query = query.where(Prompt.is_active == True)  # noqa: E712

    params = PageParams(page=page, size=size)
    paginated = await paginate(session=db, query=query, params=params)

    for prompt in paginated.items:
        prompt.project = project

    return paginated


@router.post("/{team_name}/{project_name}", response_model=PromptResponse, status_code=201)
async def create_prompt(
    team_name: str,
    project_name: str,
    payload: PromptCreate,
    db: AsyncSession = Depends(get_db),
):
    project = await get_project_or_404(team_name, project_name, db)

    dup = await db.execute(
        select(Prompt).where(Prompt.project_id == project.id, Prompt.name == payload.name)
    )
    if dup.scalars().first():
        raise HTTPException(status_code=409, detail="Prompt name already exists in this project")

    new_prompt = Prompt(
        name=payload.name,
        description=payload.description,
        project_id=project.id,
        # head_version_id stays None until first version is created
    )
    db.add(new_prompt)
    await db.commit()
    await db.refresh(new_prompt)

    new_prompt.project = project
    return new_prompt


@router.get("/{team_name}/{project_name}/{prompt_name}", response_model=PromptDetailResponse)
async def get_prompt(
    team_name: str,
    project_name: str,
    prompt_name: str,
    db: AsyncSession = Depends(get_db),
):
    project = await get_project_or_404(team_name, project_name, db)

    query = (
        select(Prompt)
        .options(selectinload(Prompt.head_version), selectinload(Prompt.versions))
        .where(Prompt.project_id == project.id, Prompt.name == prompt_name)
    )
    result = await db.execute(query)
    prompt = result.scalars().first()
    if not prompt:
        raise HTTPException(status_code=404, detail="Prompt not found")

    # Sort versions newest first
    prompt.versions = sorted(prompt.versions, key=lambda v: v.version, reverse=True)
    prompt.project = project
    return prompt


@router.patch("/{team_name}/{project_name}/{prompt_name}", response_model=PromptResponse)
async def update_prompt(
    team_name: str,
    project_name: str,
    prompt_name: str,
    payload: PromptUpdate,
    db: AsyncSession = Depends(get_db),
):
    project = await get_project_or_404(team_name, project_name, db)
    prompt = await get_prompt_or_404(project, prompt_name, db)

    if payload.description is not None:
        prompt.description = payload.description
    if payload.is_active is not None:
        prompt.is_active = payload.is_active

    await db.commit()
    await db.refresh(prompt)
    prompt.project = project
    return prompt


@router.delete("/{team_name}/{project_name}/{prompt_name}", status_code=204)
async def delete_prompt(
    team_name: str,
    project_name: str,
    prompt_name: str,
    db: AsyncSession = Depends(get_db),
):
    project = await get_project_or_404(team_name, project_name, db)
    prompt = await get_prompt_or_404(project, prompt_name, db)
    await db.delete(prompt)
    await db.commit()


# ---------------------------------------------------------------------------
# Version routes
# ---------------------------------------------------------------------------

@router.post(
    "/{team_name}/{project_name}/{prompt_name}/versions",
    response_model=VersionResponse,
    status_code=201,
)
async def create_version(
    team_name: str,
    project_name: str,
    prompt_name: str,
    payload: VersionCreate,
    db: AsyncSession = Depends(get_db),
):
    project = await get_project_or_404(team_name, project_name, db)
    prompt = await get_prompt_or_404(project, prompt_name, db)

    # Compute next version number atomically from DB
    max_ver_result = await db.execute(
        select(func.max(PromptVersion.version)).where(PromptVersion.prompt_id == prompt.id)
    )
    next_version = (max_ver_result.scalar() or 0) + 1

    new_version = PromptVersion(
        prompt_id=prompt.id,
        version=next_version,
        content=payload.content,
        variables=extract_variables(payload.content),
        model_hint=payload.model_hint,
        temperature=payload.temperature,
        max_tokens=payload.max_tokens,
        commit_message=payload.commit_message,
    )
    db.add(new_version)
    await db.flush()  # resolve new_version.id before referencing it

    prompt.head_version_id = new_version.id
    await db.commit()
    await db.refresh(new_version)
    return new_version


@router.post(
    "/{team_name}/{project_name}/{prompt_name}/rollback",
    response_model=PromptResponse,
)
async def rollback_prompt(
    team_name: str,
    project_name: str,
    prompt_name: str,
    version: int = Query(..., description="Version number to roll back to"),
    db: AsyncSession = Depends(get_db),
):
    project = await get_project_or_404(team_name, project_name, db)
    prompt = await get_prompt_or_404(project, prompt_name, db)

    version_result = await db.execute(
        select(PromptVersion).where(
            PromptVersion.prompt_id == prompt.id,
            PromptVersion.version == version,
        )
    )
    target = version_result.scalars().first()
    if not target:
        raise HTTPException(status_code=404, detail=f"Version {version} not found")

    prompt.head_version_id = target.id
    await db.commit()
    await db.refresh(prompt)

    # Re-load head_version relationship after commit
    await db.refresh(prompt, ["head_version"])
    prompt.project = project
    return prompt
