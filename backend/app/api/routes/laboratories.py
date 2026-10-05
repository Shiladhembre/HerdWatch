from typing import Annotated
from uuid import UUID
from fastapi import APIRouter, Depends, Header
from app.dependencies import DB, CurrentUser
from app.models import LabReferral
from app.schemas.laboratory import LabCreate, LabUpdate, LabResult
from app.schemas.analytics import Filters
from app.services import laboratory_service
from app.repositories.base import filtered, paginate, get_scoped
from app.utils.responses import Envelope, ok
from app.utils.serialization import record, page

router = APIRouter(prefix="/labs", tags=["Laboratory workflow"])


@router.get("", response_model=Envelope[dict])
async def listing(db: DB, user: CurrentUser, filters: Annotated[Filters, Depends()]):
    return ok(
        page(await paginate(db, filtered(LabReferral, user, filters).order_by(LabReferral.created_at.desc()), filters))
    )


@router.post("/referral", response_model=Envelope[dict], status_code=201)
async def create(payload: LabCreate, db: DB, user: CurrentUser):
    return ok(record(await laboratory_service.create(db, user, payload)))


@router.get("/{id}", response_model=Envelope[dict])
async def get(id: UUID, db: DB, user: CurrentUser):
    return ok(record(await get_scoped(db, LabReferral, id, user)))


@router.patch("/{id}/status", response_model=Envelope[dict])
async def update(id: UUID, payload: LabUpdate, db: DB, user: CurrentUser):
    return ok(record(await laboratory_service.update(db, user, id, payload)))


@router.post("/{id}/result", response_model=Envelope[dict])
async def result(
    id: UUID,
    payload: LabResult,
    db: DB,
    user: CurrentUser,
    idempotency_key: Annotated[str, Header(min_length=8, max_length=100)],
):
    """An authorised veterinarian records a supplied lab result; confirmation remains a separate clinical action."""
    return ok(record(await laboratory_service.result(db, user, id, payload, idempotency_key)))
