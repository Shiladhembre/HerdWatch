from typing import Annotated
from uuid import UUID
from fastapi import APIRouter, Depends
from app.dependencies import DB, CurrentUser
from app.models import Outbreak
from app.schemas.outbreak import OutbreakCreate, OutbreakUpdate
from app.schemas.analytics import Filters
from app.services import outbreak_service, gis_service
from app.repositories.base import filtered, paginate, get_scoped
from app.core.permissions import require_role
from app.core.constants import Role
from app.utils.responses import Envelope, ok
from app.utils.serialization import record, page

router = APIRouter(prefix="/outbreaks", tags=["Outbreak surveillance"])


@router.get("/map", response_model=Envelope[dict])
async def map_reports(db: DB, user: CurrentUser, filters: Annotated[Filters, Depends()]):
    return ok(await gis_service.geojson(db, user, filters))


@router.get("/hotspots", response_model=Envelope[dict])
async def hotspots(db: DB, user: CurrentUser, filters: Annotated[Filters, Depends()]):
    return ok(await gis_service.hotspots(db, user, filters))


@router.get("", response_model=Envelope[dict])
async def listing(db: DB, user: CurrentUser, filters: Annotated[Filters, Depends()]):
    require_role(user, Role.FIELD_WORKER, Role.VETERINARIAN, Role.DISTRICT_OFFICER)
    return ok(page(await paginate(db, filtered(Outbreak, user, filters).order_by(Outbreak.created_at.desc()), filters)))


@router.post("", response_model=Envelope[dict], status_code=201)
async def create(payload: OutbreakCreate, db: DB, user: CurrentUser):
    return ok(record(await outbreak_service.create(db, user, payload)))


@router.get("/{id}", response_model=Envelope[dict])
async def get(id: UUID, db: DB, user: CurrentUser):
    require_role(user, Role.FIELD_WORKER, Role.VETERINARIAN, Role.DISTRICT_OFFICER)
    return ok(record(await get_scoped(db, Outbreak, id, user)))


@router.patch("/{id}", response_model=Envelope[dict])
async def update(id: UUID, payload: OutbreakUpdate, db: DB, user: CurrentUser):
    return ok(record(await outbreak_service.update(db, user, id, payload)))
