from datetime import datetime
from fastapi import APIRouter, Depends, Query, HTTPException
from pydantic import BaseModel, ConfigDict
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.session import get_db
from app.models.entities import Team
from app.core.pagination import paginate, Page, PageParams

router = APIRouter(prefix="/v1/teams", tags=["Teams"])


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

async def get_team_or_404(team_id: int, db: AsyncSession) -> Team:
    result = await db.execute(select(Team).where(Team.id == team_id))
    team = result.scalars().first()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    return team


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@router.get("/", response_model=Page[TeamResponse])
async def get_all_teams(
    db: AsyncSession = Depends(get_db),
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(50, ge=1, le=100, description="Page size"),
):
    query = select(Team)
    params = PageParams(page=page, size=size)
    return await paginate(session=db, query=query, params=params)


@router.get("/{team_name}", response_model=TeamResponse)
async def get_team(team_name: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Team).where(Team.name == team_name))
    team = result.scalars().first()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    return team


@router.post("/", response_model=TeamResponse, status_code=201)
async def create_team(team: TeamCreate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Team).where(Team.name == team.name))
    if result.scalars().first():
        raise HTTPException(status_code=409, detail="Team name already exists")

    new_team = Team(name=team.name, description=team.description)
    db.add(new_team)
    await db.commit()
    await db.refresh(new_team)
    return new_team


@router.patch("/{team_id}", response_model=TeamResponse)
async def update_team(team_id: int, team: TeamUpdate, db: AsyncSession = Depends(get_db)):
    existing_team = await get_team_or_404(team_id, db)

    if team.name is not None and team.name != existing_team.name:
        name_result = await db.execute(select(Team).where(Team.name == team.name))
        if name_result.scalars().first():
            raise HTTPException(status_code=409, detail="Team name already exists")
        existing_team.name = team.name

    if team.description is not None:
        existing_team.description = team.description

    await db.commit()
    await db.refresh(existing_team)
    return existing_team


@router.delete("/{team_id}", status_code=204)
async def delete_team(team_id: int, db: AsyncSession = Depends(get_db)):
    team = await get_team_or_404(team_id, db)
    await db.delete(team)
    await db.commit()