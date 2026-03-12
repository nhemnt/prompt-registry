from datetime import datetime
from fastapi import APIRouter, Depends, Query, HTTPException
from pydantic import BaseModel, ConfigDict
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.db.session import get_db
from app.models.entities import Project, Team
from app.core.pagination import paginate, Page, PageParams

router = APIRouter(prefix="/v1/projects", tags=["Projects"])


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

class ProjectCreate(BaseModel):
    name: str
    description: str | None = None


class ProjectUpdate(BaseModel):
    description: str | None = None


class TeamNested(BaseModel):
    id: int
    name: str
    description: str | None = None
    model_config = ConfigDict(from_attributes=True)


class ProjectResponse(BaseModel):
    id: int
    name: str
    description: str | None = None
    team: TeamNested
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

@router.get("/{team_name}", response_model=Page[ProjectResponse])
async def get_all_projects(
    team_name: str,
    db: AsyncSession = Depends(get_db),
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(50, ge=1, le=100, description="Page size"),
):
    team_result = await db.execute(select(Team).where(Team.name == team_name))
    team = team_result.scalars().first()
    if not team:
        return Page(items=[], total=0, page=page, size=size, pages=0)

    query = (
        select(Project)
        .options(selectinload(Project.team))
        .where(Project.team_id == team.id)
    )
    params = PageParams(page=page, size=size)
    return await paginate(session=db, query=query, params=params)


@router.post("/{team_name}", response_model=ProjectResponse, status_code=201)
async def create_project(
    team_name: str,
    project: ProjectCreate,
    db: AsyncSession = Depends(get_db),
):
    team_result = await db.execute(select(Team).where(Team.name == team_name))
    team = team_result.scalars().first()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")

    dup_result = await db.execute(
        select(Project).where(Project.team_id == team.id, Project.name == project.name)
    )
    if dup_result.scalars().first():
        raise HTTPException(status_code=409, detail="Project name already exists in this team")

    new_project = Project(name=project.name, description=project.description, team_id=team.id)
    db.add(new_project)
    await db.commit()
    await db.refresh(new_project)
    new_project.team = team
    return new_project


@router.get("/{team_name}/{project_name}", response_model=ProjectResponse)
async def get_project(
    team_name: str,
    project_name: str,
    db: AsyncSession = Depends(get_db),
):
    project = await get_project_or_404(team_name, project_name, db)
    return project


@router.patch("/{team_name}/{project_name}", response_model=ProjectResponse)
async def update_project(
    team_name: str,
    project_name: str,
    payload: ProjectUpdate,
    db: AsyncSession = Depends(get_db),
):
    project = await get_project_or_404(team_name, project_name, db)
    if payload.description is not None:
        project.description = payload.description
    
    await db.commit()
    await db.refresh(project)
    return project


@router.delete("/{team_name}/{project_name}", status_code=204)
async def delete_project(
    team_name: str,
    project_name: str,
    db: AsyncSession = Depends(get_db),
):
    project = await get_project_or_404(team_name, project_name, db)
    await db.delete(project)
    await db.commit()