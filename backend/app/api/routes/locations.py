from uuid import UUID
from typing import Annotated
from fastapi import APIRouter, Query
from sqlalchemy import select, func
from app.dependencies import DB, CurrentUser
from app.models import Location
from app.core.constants import Role
from app.core.exceptions import DomainError
from app.utils.responses import Envelope, ok
from app.utils.serialization import record

router = APIRouter(prefix="/locations", tags=["Locations and census"])


@router.get("", response_model=Envelope[dict])
async def listing(
    db: DB,
    user: CurrentUser,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
    search: Annotated[str, Query(max_length=100)] = "",
):
    condition = True if user.role == Role.ADMIN else Location.district_normalized == user.district.casefold()
    stmt = select(Location).where(condition)
    if search:
        stmt = stmt.where(Location.village_normalized.contains(search.casefold(), autoescape=True))
    total = await db.scalar(select(func.count()).select_from(stmt.subquery()))
    rows = (await db.scalars(stmt.order_by(Location.village).offset((page - 1) * page_size).limit(page_size))).all()
    return ok(
        {
            "items": [record(r) for r in rows],
            "page": page,
            "page_size": page_size,
            "total": total,
            "pages": (total + page_size - 1) // page_size,
        }
    )


@router.get("/{id}/livestock", response_model=Envelope[dict])
async def livestock(id: UUID, db: DB, user: CurrentUser):
    row = await db.get(Location, id)
    if not row or user.role != Role.ADMIN and row.district_normalized != user.district.casefold():
        raise DomainError("LOCATION_NOT_FOUND", "Location not found.", 404)
    return ok(record(row))
