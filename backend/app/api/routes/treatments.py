from typing import Annotated
from uuid import UUID
from fastapi import APIRouter, Depends
from app.dependencies import DB, CurrentUser
from app.models import Treatment
from app.schemas.treatment import TreatmentCreate, TreatmentUpdate
from app.schemas.analytics import Filters
from app.services import treatment_service
from app.repositories.base import filtered, paginate, get_scoped
from app.utils.responses import Envelope, ok
from app.utils.serialization import record, page

router = APIRouter(prefix="/treatments", tags=["Treatment records"])


@router.get("", response_model=Envelope[dict])
async def listing(db: DB, user: CurrentUser, filters: Annotated[Filters, Depends()]):
    return ok(
        page(await paginate(db, filtered(Treatment, user, filters).order_by(Treatment.created_at.desc()), filters))
    )


@router.post("", response_model=Envelope[dict], status_code=201)
async def create(payload: TreatmentCreate, db: DB, user: CurrentUser):
    return ok(record(await treatment_service.create(db, user, payload)))


@router.get("/{id}", response_model=Envelope[dict])
async def get(id: UUID, db: DB, user: CurrentUser):
    return ok(record(await get_scoped(db, Treatment, id, user)))


@router.patch("/{id}", response_model=Envelope[dict])
async def update(id: UUID, payload: TreatmentUpdate, db: DB, user: CurrentUser):
    return ok(record(await treatment_service.update(db, user, id, payload)))
