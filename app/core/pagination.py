import math
from typing import Generic, Sequence, TypeVar, Any
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import Select

T = TypeVar("T")

class PageParams(BaseModel):
    page: int = 1
    size: int = 50

class Page(BaseModel, Generic[T]):
    items: Sequence[T]
    total: int
    page: int
    size: int
    pages: int

async def paginate(
    session: AsyncSession, 
    query: Select, 
    params: PageParams
) -> Page[T]:
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await session.execute(count_query)
    total = total_result.scalar_one()

    offset = (params.page - 1) * params.size
    paginated_query = query.offset(offset).limit(params.size)
    result = await session.execute(paginated_query)
    items = result.scalars().all()

    pages = math.ceil(total / params.size) if total > 0 else 0

    return Page(
        items=items,
        total=total,
        page=params.page,
        size=params.size,
        pages=pages
    )
