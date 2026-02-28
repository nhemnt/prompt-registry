from datetime import datetime
from fastapi import APIRouter, Depends, Query, HTTPException
from pydantic import BaseModel, ConfigDict
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.session import get_db
from app.models.entities import Teams
from app.core.pagination import paginate, Page, PageParams

router = APIRouter(prefix="/v1/teams", tags=["Teams"])


class TeamCreate(BaseModel):
    name: str
    description: str | None = None

class TeamUpdate(BaseModel):
    name: str | None = None
    description: str | None = None

class TeamResponse(BaseModel):
    id: int
    name: str
    description: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True) 

@router.get("/", response_model=Page[TeamResponse])
async def get_all_teams(
    db: AsyncSession = Depends(get_db),
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(50, ge=1, le=100, description="Page size")
):
    query = select(Teams)
    params = PageParams(page=page, size=size)
    return await paginate(session=db, query=query, params=params)

@router.get("/{team_name}", response_model = TeamResponse)
async def get_team(team_name: str, db: AsyncSession = Depends(get_db)):
    query = select(Teams).where(Teams.name == team_name)
    result = await db.execute(query)
    return result.scalars().first()
    
@router.post("/", response_model=TeamResponse)
async def create_team(team: TeamCreate, db: AsyncSession = Depends(get_db)):
    query = select(Teams).where(Teams.name == team.name)
    result = await db.execute(query)
    if result.scalars().first():
        raise HTTPException(status_code=400, detail="Team name already exists")
    
    new_team = Teams(name=team.name, description=team.description)
    db.add(new_team)
    await db.commit()
    await db.refresh(new_team)
    return new_team

@router.put("/{team_id}", response_model=TeamResponse)
async def update_team(team_id: int, team: TeamUpdate, db: AsyncSession = Depends(get_db)):
    query = select(Teams).where(Teams.id == team_id)
    result = await db.execute(query)
    existing_team = result.scalars().first()
    
    if not existing_team:
        raise HTTPException(status_code=404, detail="Team not found")
        
    if team.name is not None and team.name != existing_team.name:
        name_query = select(Teams).where(Teams.name == team.name)
        name_result = await db.execute(name_query)
        if name_result.scalars().first():
            raise HTTPException(status_code=400, detail="Team name already exists")
        existing_team.name = team.name
        
    if team.description is not None:
        existing_team.description = team.description
        
    await db.commit()
    await db.refresh(existing_team)
    return existing_team

# @router.delete("/{team_id}")
# async def delete_team(team_id: int):
#     return {"message": f"Delete Team {team_id}"}