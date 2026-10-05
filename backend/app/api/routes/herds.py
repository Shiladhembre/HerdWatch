from typing import Annotated
from uuid import UUID
from fastapi import APIRouter, Depends
from app.dependencies import DB, CurrentUser
from app.models import Herd
from app.schemas.herd import HerdCreate, HerdUpdate
from app.schemas.analytics import Filters
from app.services import animal_service
from app.repositories.base import filtered, paginate, get_scoped
from app.utils.responses import Envelope, ok
from app.utils.serialization import record, page

router = APIRouter(prefix="/herds", tags=["Herds"])


@router.get("", response_model=Envelope[dict])
async def listing(db: DB, user: CurrentUser, filters: Annotated[Filters, Depends()]):
    return ok(page(await paginate(db, filtered(Herd, user, filters).order_by(Herd.created_at.desc()), filters)))


@router.post("", response_model=Envelope[dict], status_code=201)
async def create(payload: HerdCreate, db: DB, user: CurrentUser):
    return ok(record(await animal_service.create(db, user, payload, Herd)))


@router.get("/{id}", response_model=Envelope[dict])
async def get(id: UUID, db: DB, user: CurrentUser):
    return ok(record(await get_scoped(db, Herd, id, user)))


@router.patch("/{id}", response_model=Envelope[dict])
async def update(id: UUID, payload: HerdUpdate, db: DB, user: CurrentUser):
    return ok(record(await animal_service.update(db, user, id, payload, Herd)))
