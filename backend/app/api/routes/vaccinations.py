from typing import Annotated
from uuid import UUID
from fastapi import APIRouter, Depends
from app.dependencies import DB, CurrentUser
from app.models import Vaccination
from app.schemas.vaccination import VaccinationCreate, VaccinationUpdate
from app.schemas.analytics import Filters
from app.services import vaccination_service
from app.repositories.base import filtered, paginate, get_scoped
from app.utils.responses import Envelope, ok
from app.utils.serialization import record, page

router = APIRouter(prefix="/vaccinations", tags=["Vaccination"])


@router.get("", response_model=Envelope[dict])
async def listing(db: DB, user: CurrentUser, filters: Annotated[Filters, Depends()]):
    return ok(
        page(await paginate(db, filtered(Vaccination, user, filters).order_by(Vaccination.created_at.desc()), filters))
    )


@router.post("", response_model=Envelope[dict], status_code=201)
async def create(payload: VaccinationCreate, db: DB, user: CurrentUser):
    return ok(record(await vaccination_service.create(db, user, payload)))


@router.get("/{id}", response_model=Envelope[dict])
async def get(id: UUID, db: DB, user: CurrentUser):
    return ok(record(await get_scoped(db, Vaccination, id, user)))


@router.patch("/{id}", response_model=Envelope[dict])
async def update(id: UUID, payload: VaccinationUpdate, db: DB, user: CurrentUser):
    return ok(record(await vaccination_service.update(db, user, id, payload)))
