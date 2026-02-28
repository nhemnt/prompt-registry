from datetime import datetime
from fastapi import APIRouter, Depends, Query, HTTPException
from pydantic import BaseModel, ConfigDict
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.session import get_db
from app.models.entities import Projects, Teams
from app.core.pagination import paginate, Page, PageParams


router = APIRouter(prefix="/v1/projects", tags=["Projects"])

class ProjectCreate(BaseModel):
    name: str
    description: str | None = None

class Team(BaseModel):
    id: int
    name: str
    description: str | None = None

    model_config = ConfigDict(from_attributes=True) 

class ProjectResponse(BaseModel):
    id: int
    name: str
    description: str | None = None
    team: Team
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

@router.get("/{team_name}", response_model=Page[ProjectResponse])
async def get_all_projects(
    team_name: str,
    db: AsyncSession = Depends(get_db),
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(50, ge=1, le=100, description="Page size")
):
    team_query = select(Teams).where(Teams.name == team_name)
    team_result = await db.execute(team_query)
    team = team_result.scalars().first()
    
    if not team:
        return Page(items=[], total=0, page=page, size=size, pages=0)

    query = select(Projects).where(Projects.team_id == team.id)
    params = PageParams(page=page, size=size)
    paginated = await paginate(session=db, query=query, params=params)
    
    for project in paginated.items:
        project.team = team
        
    return paginated

@router.post("/{team_name}", response_model=ProjectResponse)
async def create_project(team_name: str, project: ProjectCreate, db: AsyncSession = Depends(get_db)):
    query = select(Teams).where(Teams.name == team_name)
    result = await db.execute(query)
    team = result.scalars().first()
    
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
        
    project_query = select(Projects).where(Projects.name == project.name)
    project_result = await db.execute(project_query)
    if project_result.scalars().first():
        raise HTTPException(status_code=400, detail="Project name already exists")
    
    new_project = Projects(name=project.name, description=project.description, team_id=team.id)
    db.add(new_project)
    await db.commit()
    await db.refresh(new_project)
    
    new_project.team = team
    return new_project